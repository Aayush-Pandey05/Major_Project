import { Test, TestingModule } from '@nestjs/testing';
import { ChatService } from '../src/modules/chat/chat.service';
import { PrismaService } from '../src/database/prisma.service';

describe('ChatService - 10 Conversation Retention Policy', () => {
  let chatService: ChatService;
  let prismaService: PrismaService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [ChatService, PrismaService],
    }).compile();

    chatService = module.get<ChatService>(ChatService);
    prismaService = module.get<PrismaService>(PrismaService);
  });

  it('should enforce the maximum 10-conversation limit per anonymous session', async () => {
    const anonymousId = `test_anon_${Date.now()}`;

    // Create 12 sessions sequentially
    for (let i = 1; i <= 12; i++) {
      await chatService.createSession(anonymousId, `Analysis Thread #${i}`);
    }

    const sessions = await chatService.getRecentSessions(anonymousId);
    expect(sessions.length).toBeLessThanOrEqual(10);
    expect(sessions.length).toBe(10);

    // Most recent thread should be #12
    expect(sessions[0].title).toBe('Analysis Thread #12');
  });

  it('should allow adding messages and reopening conversation history', async () => {
    const anonymousId = `test_anon_msg_${Date.now()}`;
    const session = await chatService.createSession(anonymousId, 'Sales Inquiry');

    await chatService.addMessage(session.id, 'user', 'Forecast sales for next 14 days');
    await chatService.addMessage(session.id, 'assistant', 'Projected sales total 15,200 units.', 'forecasting', {
      horizon: 14,
    });

    const loaded = await chatService.getSessionById(session.id);
    expect(loaded.messages.length).toBe(2);
    expect(loaded.messages[0].role).toBe('user');
    expect(loaded.messages[1].role).toBe('assistant');
  });
});
