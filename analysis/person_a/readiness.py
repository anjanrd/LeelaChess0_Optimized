"""Show the reminder/dependencies before Run 2; this never launches a job."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def assess(progress,dependencies):
    status=progress.get('steps',{}).get('A5',{}).get('status','not completed')
    a5_clear=status=='verified' or bool(progress.get('A5_handling_explicitly_accepted',False))
    waits=[key for key,item in dependencies.items() if item.get('status')!='RECEIVED_AND_REVIEWED']
    return {'ready_for_run2':a5_clear and not waits,'A5_status':status,
            'A5_reminder_required':not a5_clear,'Ritwik_handoffs_to_review':waits,
            'note':'Availability/markers are not experimental validity or permission to launch GPU jobs.'}


def main():
    folder=ROOT/'analysis/person_a/run1'
    p=json.loads((folder/'progress.json').read_text())
    deps=json.loads((folder/'ritwik_dependencies.json').read_text())
    result=assess(p,deps)
    if result['A5_reminder_required']:
        print('REMINDER: address deferred A5 before autonomous Run 2. Read analysis/person_a/BEFORE_RUN_2.md.')
    print(json.dumps(result,indent=2))
    # Missing handoffs are an expected waiting state, not an experiment failure.


if __name__=='__main__':
    main()
