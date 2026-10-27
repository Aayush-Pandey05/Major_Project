import { Module } from '@nestjs/common';
import { AgentGatewayController } from './agent-gateway.controller';
import { AgentGatewayService } from './agent-gateway.service';
import { ChatModule } from '../chat/chat.module';
import { DatasetsModule } from '../datasets/datasets.module';
import { DatabaseConnectionsModule } from '../database-connections/database-connections.module';

@Module({
  imports: [ChatModule, DatasetsModule, DatabaseConnectionsModule],
  controllers: [AgentGatewayController],
  providers: [AgentGatewayService],
  exports: [AgentGatewayService],
})
export class AgentGatewayModule {}
