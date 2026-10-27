import { Module } from '@nestjs/common';
import { ModelEvaluationsController } from './model-evaluations.controller';
import { ModelEvaluationsService } from './model-evaluations.service';

@Module({
  controllers: [ModelEvaluationsController],
  providers: [ModelEvaluationsService],
  exports: [ModelEvaluationsService],
})
export class ModelEvaluationsModule {}
