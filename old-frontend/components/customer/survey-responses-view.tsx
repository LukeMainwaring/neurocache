import { IntakeSurvey } from '@/client/types.gen'

const INTAKE_OPENING_QUESTION =
  'Can you tell me what feeling good about money would look like for you three months from now?'

const INTAKE_QUESTION_1 =
  'Why do you want to make a change with your money right now?'
const INTAKE_QUESTION_2 =
  'When you look at a typical month, where does most of your money go?'
const INTAKE_QUESTION_3 =
  'What usually gets in the way when you try to stick with your money goals?'

export function SurveyResponsesView({
  intakeSurvey
}: {
  intakeSurvey: IntakeSurvey
}) {
  if (!intakeSurvey) {
    return <div>No survey data available</div>
  }

  return (
    <div className="space-y-8">
      <div className="space-y-6">
        <div>
          <h4 className="text-base mb-1 font-semibold">
            {INTAKE_OPENING_QUESTION}
          </h4>
          <p className="text-sm text-muted-foreground">
            {intakeSurvey.opening_question_response}
          </p>
        </div>
      </div>
      <div className="space-y-6">
        <div>
          <h4 className="text-base mb-1 font-semibold">{INTAKE_QUESTION_1}</h4>
          <p className="text-sm text-muted-foreground">
            {intakeSurvey.question_1_response}
          </p>
        </div>
      </div>
      <div className="space-y-6">
        <div>
          <h4 className="text-base mb-1 font-semibold">{INTAKE_QUESTION_2}</h4>
          <p className="text-sm text-muted-foreground">
            {intakeSurvey.question_2_response}
          </p>
        </div>
      </div>
      <div className="space-y-6">
        <div>
          <h4 className="text-base mb-1 font-semibold">{INTAKE_QUESTION_3}</h4>
          <p className="text-sm text-muted-foreground">
            {intakeSurvey.question_3_response}
          </p>
        </div>
      </div>
      <div className="space-y-6">
        <div>
          <h4 className="text-base mb-1 font-semibold">Generated Plan</h4>
          <p className="text-sm text-muted-foreground">
            {intakeSurvey.generated_plan}
          </p>
        </div>
      </div>
    </div>
  )
}
