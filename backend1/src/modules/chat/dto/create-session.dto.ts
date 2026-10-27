import { IsOptional, IsString } from 'class-validator';

export class CreateSessionDto {
  @IsOptional()
  @IsString()
  anonymousSessionId?: string;

  @IsOptional()
  @IsString()
  title?: string;
}

export class SendMessageDto {
  @IsString()
  sessionId: string;

  @IsString()
  content: string;

  @IsOptional()
  @IsString()
  anonymousSessionId?: string;
}
