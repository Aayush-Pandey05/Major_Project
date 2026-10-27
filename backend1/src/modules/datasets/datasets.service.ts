import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { PrismaService } from '../../database/prisma.service';

@Injectable()
export class DatasetsService {
  private readonly logger = new Logger(DatasetsService.name);
  private readonly backend2Url: string;
  private readonly uploadsDir: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
  ) {
    this.backend2Url = this.configService.get<string>('backend2Url');
    this.uploadsDir = this.configService.get<string>('uploadsDir');
    if (!fs.existsSync(this.uploadsDir)) {
      fs.mkdirSync(this.uploadsDir, { recursive: true });
    }
  }

  computeChecksum(filePath: string): string {
    const fileBuffer = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(fileBuffer).digest('hex');
  }

  async processUpload(file: Express.Multer.File, anonymousSessionId = 'default_session') {
    const checksum = this.computeChecksum(file.path);

    // Call Backend 2 to profile the dataset
    let profileData: any = {};
    try {
      const resp = await axios.post(`${this.backend2Url}/api/v1/datasets/profile`, {
        file_path: file.path,
      });
      profileData = resp.data;
    } catch (err) {
      this.logger.warn(`Backend 2 profiling call failed: ${err.message}. Generating basic profile.`);
      profileData = {
        row_count: 0,
        column_count: 0,
        columns: [],
        error: err.message,
      };
    }

    const datasetRecord = {
      anonymousSessionId,
      originalFilename: file.originalname,
      storedFilename: path.basename(file.path),
      filePath: file.path,
      sha256Checksum: checksum,
      rowCount: profileData.row_count || 0,
      columnCount: profileData.column_count || 0,
      metadataJson: profileData,
    };

    const saved = await this.prisma.saveDatasetMeta(datasetRecord);
    return {
      ...saved,
      profile: profileData,
    };
  }

  async getDatasets(anonymousSessionId = 'default_session') {
    return this.prisma.getDatasets(anonymousSessionId);
  }

  async getDatasetById(id: string) {
    const dataset = await this.prisma.getDatasetById(id);
    if (!dataset) {
      throw new NotFoundException(`Dataset ${id} not found.`);
    }
    return dataset;
  }
}
