import { Controller, Post, Body, Res } from '@nestjs/common';
import { Response } from 'express';
import { AgentGatewayService, AgentQueryDto } from './agent-gateway.service';

@Controller('agent-gateway')
export class AgentGatewayController {
  constructor(private readonly agentGatewayService: AgentGatewayService) {}

  @Post('query')
  async executeQuery(@Body() dto: AgentQueryDto) {
    return this.agentGatewayService.executeQuery(dto);
  }

  @Post('stream')
  async streamQuery(@Body() dto: AgentQueryDto, @Res() res: Response) {
    return this.agentGatewayService.streamQuery(dto, res);
  }
}
