import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import { Response } from 'express';
import { PrismaService } from '../../database/prisma.service';
import { ChatService } from '../chat/chat.service';
import { DatasetsService } from '../datasets/datasets.service';
import { DatabaseConnectionsService } from '../database-connections/database-connections.service';

export interface AgentQueryDto {
  query: string;
  sessionId?: string;
  datasetId?: string;
  connectionId?: string;
  anonymousSessionId?: string;
}

@Injectable()
export class AgentGatewayService {
  private readonly logger = new Logger(AgentGatewayService.name);
  private readonly backend2Url: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
    private readonly chatService: ChatService,
    private readonly datasetsService: DatasetsService,
    private readonly dbConnectionsService: DatabaseConnectionsService,
  ) {
    this.backend2Url = this.configService.get<string>('backend2Url');
  }

  async executeQuery(dto: AgentQueryDto) {
    // 1. Resolve or create chat session
    let sessionId = dto.sessionId;
    if (!sessionId) {
      const session = await this.chatService.createSession(
        dto.anonymousSessionId || 'default_session',
        dto.query.slice(0, 40) + '...',
      );
      sessionId = session.id;
    }

    // 2. Fetch existing session history before appending the new query (for conversational context)
    const existingSession = await this.chatService.getSessionById(sessionId).catch(() => null);
    const existingMessages = existingSession?.messages || [];
    const chatHistory = existingMessages.slice(-6).map((m: any) => ({
      role: m.role,
      content: m.content,
      planIntent: m.planIntent,
    }));
    const lastAssistantMessage = [...existingMessages]
      .reverse()
      .find((m: any) => m.role === 'assistant' && m.structuredData);
    const previousResults = lastAssistantMessage?.structuredData || null;

    // 3. Resolve dataset path or database connection URL if provided, with session fallback
    let datasetPath: string | undefined;
    let datasetMetadata: any;
    if (dto.datasetId) {
      try {
        const ds = await this.datasetsService.getDatasetById(dto.datasetId);
        datasetPath = ds.filePath;
        datasetMetadata = ds.metadataJson;
      } catch (e) {
        this.logger.warn(`Dataset lookup failed: ${e.message}`);
      }
    } else {
      try {
        const userDatasets = await this.datasetsService.getDatasets(dto.anonymousSessionId || 'default_session');
        if (userDatasets && userDatasets.length > 0) {
          datasetPath = userDatasets[0].filePath;
          datasetMetadata = userDatasets[0].metadataJson;
        }
      } catch (e) {
        this.logger.debug(`No recent dataset for session: ${e.message}`);
      }
    }

    let dbUrl: string | undefined;
    if (dto.connectionId) {
      dbUrl = this.dbConnectionsService.getConnectionRawUrl(dto.connectionId);
    }

    // 4. Save user message to chat history
    await this.chatService.addMessage(sessionId, 'user', dto.query);

    // 5. Call Python Backend 2 LangGraph agent workflow with conversational context
    const startTime = Date.now();
    let backend2Response: any;
    try {
      const resp = await axios.post(`${this.backend2Url}/api/v1/agents/execute`, {
        query: dto.query,
        session_id: sessionId,
        dataset_path: datasetPath,
        dataset_metadata: datasetMetadata,
        db_connection_url: dbUrl,
        chat_history: chatHistory,
        previous_results: previousResults,
      });
      backend2Response = resp.data;
    } catch (err) {
      this.logger.error(`Backend 2 agent execution error: ${err.message}`);
      const errorMsg = err.response?.data?.detail || err.message;
      await this.chatService.addMessage(
        sessionId,
        'assistant',
        `An error occurred while executing the analytical agents: ${errorMsg}`,
      );
      return {
        sessionId,
        error: errorMsg,
      };
    }

    const executionTimeMs = Date.now() - startTime;
    const finalResp = backend2Response.response || {};

    // 6. Save assistant answer with structured metadata to chat history
    await this.chatService.addMessage(
      sessionId,
      'assistant',
      finalResp.answer || 'Analysis completed.',
      backend2Response.plan_intent,
      finalResp,
    );

    return {
      sessionId,
      planIntent: backend2Response.plan_intent,
      targetAgents: backend2Response.target_agents,
      progressEvents: backend2Response.progress_events || [],
      response: finalResp,
      executionTimeMs,
    };
  }

  async streamQuery(dto: AgentQueryDto, res: Response) {
    let sessionId = dto.sessionId;
    if (!sessionId) {
      const session = await this.chatService.createSession(
        dto.anonymousSessionId || 'default_session',
        dto.query.slice(0, 40) + '...',
      );
      sessionId = session.id;
    }

    // Fetch existing session messages for multi-turn conversational context
    const existingSession = await this.chatService.getSessionById(sessionId).catch(() => null);
    const existingMessages = existingSession?.messages || [];
    const chatHistory = existingMessages.slice(-6).map((m: any) => ({
      role: m.role,
      content: m.content,
      planIntent: m.planIntent,
    }));
    const lastAssistantMessage = [...existingMessages]
      .reverse()
      .find((m: any) => m.role === 'assistant' && m.structuredData);
    const previousResults = lastAssistantMessage?.structuredData || null;

    let datasetPath: string | undefined;
    let datasetMetadata: any;
    if (dto.datasetId) {
      try {
        const ds = await this.datasetsService.getDatasetById(dto.datasetId);
        datasetPath = ds.filePath;
        datasetMetadata = ds.metadataJson;
      } catch (e) {
        this.logger.warn(`Dataset lookup failed: ${e.message}`);
      }
    } else {
      try {
        const userDatasets = await this.datasetsService.getDatasets(dto.anonymousSessionId || 'default_session');
        if (userDatasets && userDatasets.length > 0) {
          datasetPath = userDatasets[0].filePath;
          datasetMetadata = userDatasets[0].metadataJson;
        }
      } catch (e) {
        this.logger.debug(`No recent dataset for session: ${e.message}`);
      }
    }

    let dbUrl: string | undefined;
    if (dto.connectionId) {
      dbUrl = this.dbConnectionsService.getConnectionRawUrl(dto.connectionId);
    }

    await this.chatService.addMessage(sessionId, 'user', dto.query);

    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    // Stream from Backend 2 with conversational context
    try {
      const streamResp = await axios.post(
        `${this.backend2Url}/api/v1/agents/stream`,
        {
          query: dto.query,
          session_id: sessionId,
          dataset_path: datasetPath,
          dataset_metadata: datasetMetadata,
          db_connection_url: dbUrl,
          chat_history: chatHistory,
          previous_results: previousResults,
        },
        { responseType: 'stream' },
      );

      let accumulatedAnswer = '';
      let finalDataObj: any = null;

      streamResp.data.on('data', (chunk: Buffer) => {
        const text = chunk.toString();
        res.write(text);

        // Check if final_response arrived to record in DB
        if (text.includes('event: final_response')) {
          try {
            const dataMatch = text.match(/data:\s*({.*})/);
            if (dataMatch && dataMatch[1]) {
              finalDataObj = JSON.parse(dataMatch[1]);
              accumulatedAnswer = finalDataObj.answer || 'Analysis completed.';
            }
          } catch (e) {
            this.logger.debug(`Could not parse final_response stream chunk: ${e.message}`);
          }
        }
      });

      streamResp.data.on('end', async () => {
        if (accumulatedAnswer) {
          await this.chatService.addMessage(
            sessionId,
            'assistant',
            accumulatedAnswer,
            'streamed',
            finalDataObj,
          );
        }
        res.end();
      });

      streamResp.data.on('error', (err: any) => {
        this.logger.error(`Stream error from Backend 2: ${err.message}`);
        res.write(`event: error\ndata: ${JSON.stringify({ error: err.message })}\n\n`);
        res.end();
      });
    } catch (err) {
      this.logger.error(`Failed to initiate stream with Backend 2: ${err.message}`);
      res.write(`event: error\ndata: ${JSON.stringify({ error: err.message })}\n\n`);
      res.end();
    }
  }
}
