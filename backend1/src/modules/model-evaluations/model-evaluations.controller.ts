import { Controller, Get } from '@nestjs/common';
import { ModelEvaluationsService } from './model-evaluations.service';

@Controller('model-evaluations')
export class ModelEvaluationsController {
  constructor(private readonly service: ModelEvaluationsService) {}

  @Get()
  async getEvaluations() {
    return this.service.getEvaluations();
  }
}
