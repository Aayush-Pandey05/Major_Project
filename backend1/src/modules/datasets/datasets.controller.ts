import {
  Controller,
  Get,
  Post,
  Param,
  Query,
  UseInterceptors,
  UploadedFile,
  Body,
  BadRequestException,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import * as path from 'path';
import * as fs from 'fs';
import { DatasetsService } from './datasets.service';

@Controller('datasets')
export class DatasetsController {
  constructor(private readonly datasetsService: DatasetsService) {}

  @Post('upload')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: diskStorage({
        destination: (req, file, cb) => {
          const uploadsDir = process.env.UPLOADS_DIR
            ? path.resolve(process.env.UPLOADS_DIR)
            : path.resolve(process.cwd(), '../backend2/storage/uploads');
          if (!fs.existsSync(uploadsDir)) {
            fs.mkdirSync(uploadsDir, { recursive: true });
          }
          cb(null, uploadsDir);
        },
        filename: (req, file, cb) => {
          const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
          const ext = path.extname(file.originalname);
          cb(null, `dataset-${uniqueSuffix}${ext}`);
        },
      }),
      limits: {
        fileSize: 50 * 1024 * 1024, // 50MB
      },
      fileFilter: (req, file, cb) => {
        const ext = path.extname(file.originalname).toLowerCase();
        if (['.csv', '.xlsx', '.xls', '.parquet'].includes(ext)) {
          cb(null, true);
        } else {
          cb(new BadRequestException('Only CSV, Excel, and Parquet files are supported.'), false);
        }
      },
    }),
  )
  async uploadDataset(
    @UploadedFile() file: Express.Multer.File,
    @Body('anonymousSessionId') anonymousSessionId?: string,
  ) {
    if (!file) {
      throw new BadRequestException('No file uploaded.');
    }
    return this.datasetsService.processUpload(file, anonymousSessionId || 'default_session');
  }

  @Get()
  async getDatasets(@Query('anonymousSessionId') anonymousSessionId?: string) {
    return this.datasetsService.getDatasets(anonymousSessionId || 'default_session');
  }

  @Get(':id')
  async getDatasetById(@Param('id') id: string) {
    return this.datasetsService.getDatasetById(id);
  }
}
