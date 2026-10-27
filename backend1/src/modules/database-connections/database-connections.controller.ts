import { Controller, Post, Get, Body, Query } from '@nestjs/common';
import { DatabaseConnectionsService, DatabaseConnectionDto } from './database-connections.service';

@Controller('database-connections')
export class DatabaseConnectionsController {
  constructor(private readonly dbService: DatabaseConnectionsService) {}

  @Post('test')
  async testConnection(@Body('connectionUrl') connectionUrl: string) {
    return this.dbService.testConnection(connectionUrl);
  }

  @Post('schema')
  async getSchema(@Body('connectionUrl') connectionUrl: string) {
    return this.dbService.getSchema(connectionUrl);
  }

  @Post()
  async saveConnection(@Body() dto: DatabaseConnectionDto) {
    return this.dbService.saveConnection(dto);
  }

  @Get()
  async getConnections(@Query('anonymousSessionId') anonymousSessionId?: string) {
    return this.dbService.getConnections(anonymousSessionId || 'default_session');
  }
}
