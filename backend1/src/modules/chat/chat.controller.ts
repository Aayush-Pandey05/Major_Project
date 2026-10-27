import { Controller, Get, Post, Delete, Body, Param, Query } from '@nestjs/common';
import { ChatService } from './chat.service';
import { CreateSessionDto, SendMessageDto } from './dto/create-session.dto';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post('sessions')
  async createSession(@Body() dto: CreateSessionDto) {
    return this.chatService.createSession(dto.anonymousSessionId, dto.title);
  }

  @Get('sessions')
  async getRecentSessions(@Query('anonymousSessionId') anonymousSessionId?: string) {
    return this.chatService.getRecentSessions(anonymousSessionId || 'default_session');
  }

  @Get('sessions/:id')
  async getSessionById(@Param('id') id: string) {
    return this.chatService.getSessionById(id);
  }

  @Delete('sessions/:id')
  async deleteSession(@Param('id') id: string) {
    return this.chatService.deleteSession(id);
  }

  @Post('messages')
  async addMessage(@Body() dto: SendMessageDto) {
    return this.chatService.addMessage(dto.sessionId, 'user', dto.content);
  }
}
