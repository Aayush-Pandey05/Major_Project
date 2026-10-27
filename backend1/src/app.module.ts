import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration from './config/configuration';
import { DatabaseModule } from './database/database.module';
import { ChatModule } from './modules/chat/chat.module';
import { DatasetsModule } from './modules/datasets/datasets.module';
import { DatabaseConnectionsModule } from './modules/database-connections/database-connections.module';
import { AgentGatewayModule } from './modules/agent-gateway/agent-gateway.module';
import { ModelEvaluationsModule } from './modules/model-evaluations/model-evaluations.module';
import { ResultsModule } from './modules/results/results.module';
import { HealthModule } from './modules/health/health.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['../.env', '.env'],
    }),
    DatabaseModule,
    ChatModule,
    DatasetsModule,
    DatabaseConnectionsModule,
    AgentGatewayModule,
    ModelEvaluationsModule,
    ResultsModule,
    HealthModule,
  ],
})
export class AppModule {}
