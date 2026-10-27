import { Controller, Get, Param, Res } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Response } from 'express';
import axios from 'axios';

@Controller('results')
export class ResultsController {
  private readonly backend2Url: string;

  constructor(private readonly configService: ConfigService) {
    this.backend2Url = this.configService.get<string>('backend2Url');
  }

  @Get('download/:filename')
  async downloadResult(@Param('filename') filename: string, @Res() res: Response) {
    try {
      const response = await axios.get(`${this.backend2Url}/api/v1/results/download/${filename}`, {
        responseType: 'stream',
      });
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
      const contentType = (response.headers['content-type'] as string) || 'application/octet-stream';
      res.setHeader('Content-Type', contentType);
      response.data.pipe(res);
    } catch (err) {
      res.status(404).json({ error: 'Result file not found.' });
    }
  }
}
