import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';

@Injectable()
export class ModelEvaluationsService {
  private readonly logger = new Logger(ModelEvaluationsService.name);
  private readonly backend2Url: string;

  constructor(private readonly configService: ConfigService) {
    this.backend2Url = this.configService.get<string>('backend2Url');
  }

  async getEvaluations() {
    try {
      const resp = await axios.get(`${this.backend2Url}/api/v1/evaluations`);
      return resp.data;
    } catch (err) {
      this.logger.error(`Failed to retrieve model evaluations from Backend 2: ${err.message}`);
      return {
        anomaly_detection: { error: 'Unavailable' },
        forecasting: { error: 'Unavailable' },
      };
    }
  }
}
