import { Module } from '@nestjs/common';
import { DatabaseConnectionsController } from './database-connections.controller';
import { DatabaseConnectionsService } from './database-connections.service';

@Module({
  controllers: [DatabaseConnectionsController],
  providers: [DatabaseConnectionsService],
  exports: [DatabaseConnectionsService],
})
export class DatabaseConnectionsModule {}
