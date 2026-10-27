import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import { PrismaService } from '../../database/prisma.service';

export interface DatabaseConnectionDto {
  name: string;
  type: string;
  connectionUrl: string;
  anonymousSessionId?: string;
}

@Injectable()
export class DatabaseConnectionsService {
  private readonly logger = new Logger(DatabaseConnectionsService.name);
  private readonly backend2Url: string;
  private memoryConnections = new Map<string, any>();

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
  ) {
    this.backend2Url = this.configService.get<string>('backend2Url');
  }

  async testConnection(connectionUrl: string) {
    try {
      const resp = await axios.post(`${this.backend2Url}/api/v1/database/test`, {
        connection_url: connectionUrl,
      });
      return resp.data;
    } catch (err) {
      this.logger.error(`Database test failed: ${err.message}`);
      return {
        success: false,
        message: err.response?.data?.detail || err.message,
      };
    }
  }

  async getSchema(connectionUrl: string) {
    try {
      const resp = await axios.post(`${this.backend2Url}/api/v1/database/schema`, {
        connection_url: connectionUrl,
      });
      return resp.data;
    } catch (err) {
      this.logger.error(`Schema fetch failed: ${err.message}`);
      return {
        tables_count: 0,
        tables: [],
        error: err.response?.data?.detail || err.message,
      };
    }
  }

  async saveConnection(dto: DatabaseConnectionDto) {
    const id = `conn_${Date.now()}`;
    // Mask password in stored representation
    const sanitizedUrl = dto.connectionUrl.replace(/:([^@]+)@/, ':****@');
    const record = {
      id,
      name: dto.name,
      type: dto.type,
      sanitizedUrl,
      rawUrl: dto.connectionUrl, // Kept server-side only
      anonymousSessionId: dto.anonymousSessionId || 'default_session',
      createdAt: new Date(),
    };
    this.memoryConnections.set(id, record);

    // Return sanitized metadata only
    return {
      id: record.id,
      name: record.name,
      type: record.type,
      sanitizedUrl: record.sanitizedUrl,
      createdAt: record.createdAt,
    };
  }

  async getConnections(anonymousSessionId = 'default_session') {
    return Array.from(this.memoryConnections.values())
      .filter((c) => c.anonymousSessionId === anonymousSessionId)
      .map((c) => ({
        id: c.id,
        name: c.name,
        type: c.type,
        sanitizedUrl: c.sanitizedUrl,
        createdAt: c.createdAt,
      }));
  }

  getConnectionRawUrl(id: string): string | null {
    const conn = this.memoryConnections.get(id);
    return conn ? conn.rawUrl : null;
  }
}
