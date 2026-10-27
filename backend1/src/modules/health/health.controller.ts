import { Controller, Get } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import { PrismaService } from '../../database/prisma.service';

@Controller('health')
export class HealthController {
  private readonly backend2Url: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
  ) {
    this.backend2Url = this.configService.get<string>('backend2Url');
  }

  @Get()
  async getHealth() {
    let backend2Health = { status: 'unreachable' };
    try {
      const resp = await axios.get(`${this.backend2Url}/health`, { timeout: 3000 });
      backend2Health = resp.data;
    } catch (e) {
      backend2Health = { status: 'unreachable', error: e.message } as any;
    }

    return {
      status: 'healthy',
      backend1: {
        service: 'NestJS Backend 1',
        databaseConnected: this.prisma.isConnected,
        persistenceMode: this.prisma.isConnected ? 'Neon PostgreSQL (Prisma)' : 'Local Resilient Session Store',
      },
      backend2: backend2Health,
      timestamp: new Date().toISOString(),
    };
  }
}
