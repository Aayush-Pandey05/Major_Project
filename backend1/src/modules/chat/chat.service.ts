import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../database/prisma.service';

@Injectable()
export class ChatService {
  constructor(private readonly prisma: PrismaService) {}

  async createSession(anonymousSessionId = 'default_session', title = 'New Analysis') {
    return this.prisma.createSession(anonymousSessionId, title);
  }

  async getRecentSessions(anonymousSessionId = 'default_session') {
    return this.prisma.getRecentSessions(anonymousSessionId);
  }

  async getSessionById(sessionId: string) {
    const session = await this.prisma.getSessionById(sessionId);
    if (!session) {
      throw new NotFoundException(`Chat session ${sessionId} not found.`);
    }
    return session;
  }

  async deleteSession(sessionId: string) {
    const deleted = await this.prisma.deleteSession(sessionId);
    if (!deleted) {
      throw new NotFoundException(`Chat session ${sessionId} not found or already deleted.`);
    }
    return { success: true, message: `Session ${sessionId} deleted successfully.` };
  }

  async addMessage(sessionId: string, role: string, content: string, planIntent?: string, structuredData?: any) {
    return this.prisma.addMessage(sessionId, role, content, planIntent, structuredData);
  }
}
