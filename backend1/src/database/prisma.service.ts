import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

export interface InMemoryChatSession {
  id: string;
  anonymousSessionId: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: InMemoryChatMessage[];
}

export interface InMemoryChatMessage {
  id: string;
  sessionId: string;
  role: string;
  content: string;
  planIntent?: string;
  structuredData?: any;
  createdAt: Date;
}

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PrismaService.name);
  public isConnected = false;

  // Resilient memory store for local development before Neon DB credentials are set
  private memorySessions = new Map<string, InMemoryChatSession>();
  private memoryDatasets: any[] = [];
  private memoryDataSources: any[] = [];
  private memoryAgentRuns: any[] = [];

  constructor() {
    super({
      log: process.env.NODE_ENV === 'development' ? ['warn', 'error'] : ['error'],
    });
  }

  async onModuleInit() {
    const dbUrl = process.env.DATABASE_URL;
    if (!dbUrl || dbUrl.trim() === '' || dbUrl.includes('placeholder')) {
      this.logger.warn('DATABASE_URL is not configured. Running in resilient local session mode.');
      return;
    }

    try {
      await this.$connect();
      this.isConnected = true;
      this.logger.log('Connected to Neon PostgreSQL database via Prisma.');
    } catch (error) {
      this.logger.warn(`Could not connect to Neon DB: ${error.message}. Fallback to local session mode.`);
      this.isConnected = false;
    }
  }

  async onModuleDestroy() {
    if (this.isConnected) {
      await this.$disconnect();
    }
  }

  private sessionCounter = 0;

  async createSession(anonymousSessionId: string, title = 'New Analysis'): Promise<any> {
    if (this.isConnected) {
      const session = await this.chatSession.create({
        data: {
          anonymousSessionId,
          title,
        },
      });
      await this.enforceTenConversationLimit(anonymousSessionId);
      return session;
    }

    const id = `session_${Date.now()}_${++this.sessionCounter}`;
    const newSession: InMemoryChatSession & { order: number } = {
      id,
      anonymousSessionId,
      title,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      order: this.sessionCounter,
    };
    this.memorySessions.set(id, newSession);
    this.enforceMemoryTenLimit(anonymousSessionId);
    return newSession;
  }

  async getRecentSessions(anonymousSessionId: string): Promise<any[]> {
    if (this.isConnected) {
      return this.chatSession.findMany({
        where: { anonymousSessionId },
        orderBy: { updatedAt: 'desc' },
        take: 10,
        include: {
          messages: {
            orderBy: { createdAt: 'asc' },
          },
        },
      });
    }

    return Array.from(this.memorySessions.values())
      .filter((s) => s.anonymousSessionId === anonymousSessionId)
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime() || ((b as any).order || 0) - ((a as any).order || 0))
      .slice(0, 10);
  }

  async getSessionById(sessionId: string): Promise<any> {
    if (this.isConnected) {
      return this.chatSession.findUnique({
        where: { id: sessionId },
        include: {
          messages: {
            orderBy: { createdAt: 'asc' },
          },
        },
      });
    }

    return this.memorySessions.get(sessionId) || null;
  }

  async deleteSession(sessionId: string): Promise<boolean> {
    if (this.isConnected) {
      try {
        await this.chatSession.delete({
          where: { id: sessionId },
        });
        return true;
      } catch {
        return false;
      }
    }

    return this.memorySessions.delete(sessionId);
  }

  async addMessage(
    sessionId: string,
    role: string,
    content: string,
    planIntent?: string,
    structuredData?: any,
  ): Promise<any> {
    if (this.isConnected) {
      const msg = await this.chatMessage.create({
        data: {
          sessionId,
          role,
          content,
          planIntent,
          structuredData: structuredData || undefined,
        },
      });

      // Update session activity timestamp
      await this.chatSession.update({
        where: { id: sessionId },
        data: { updatedAt: new Date() },
      });

      return msg;
    }

    const session = this.memorySessions.get(sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found.`);
    }

    const msg: InMemoryChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      sessionId,
      role,
      content,
      planIntent,
      structuredData,
      createdAt: new Date(),
    };
    session.messages.push(msg);
    session.updatedAt = new Date();
    return msg;
  }

  private async enforceTenConversationLimit(anonymousSessionId: string): Promise<void> {
    const sessions = await this.chatSession.findMany({
      where: { anonymousSessionId },
      orderBy: { updatedAt: 'desc' },
      select: { id: true },
    });

    if (sessions.length > 10) {
      const sessionsToDelete = sessions.slice(10);
      const deleteIds = sessionsToDelete.map((s) => s.id);
      await this.chatSession.deleteMany({
        where: { id: { in: deleteIds } },
      });
      this.logger.log(`Enforced 10-conversation limit: Removed ${deleteIds.length} oldest sessions.`);
    }
  }

  private enforceMemoryTenLimit(anonymousSessionId: string): void {
    const userSessions = Array.from(this.memorySessions.values())
      .filter((s) => s.anonymousSessionId === anonymousSessionId)
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime() || ((b as any).order || 0) - ((a as any).order || 0));

    if (userSessions.length > 10) {
      const excess = userSessions.slice(10);
      for (const s of excess) {
        this.memorySessions.delete(s.id);
      }
    }
  }

  // --- Datasets & DataSources In-Memory Helpers ---

  async saveDatasetMeta(dataset: any): Promise<any> {
    if (this.isConnected) {
      return this.dataset.create({ data: dataset });
    }
    const record = { id: `ds_${Date.now()}`, ...dataset, createdAt: new Date() };
    this.memoryDatasets.push(record);
    return record;
  }

  async getDatasets(anonymousSessionId: string): Promise<any[]> {
    if (this.isConnected) {
      return this.dataset.findMany({
        where: { anonymousSessionId },
        orderBy: { createdAt: 'desc' },
      });
    }
    return this.memoryDatasets.filter((d) => d.anonymousSessionId === anonymousSessionId);
  }

  async getDatasetById(id: string): Promise<any> {
    if (this.isConnected) {
      return this.dataset.findUnique({ where: { id } });
    }
    return this.memoryDatasets.find((d) => d.id === id) || null;
  }
}
