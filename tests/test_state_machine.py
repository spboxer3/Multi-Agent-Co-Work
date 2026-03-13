from runtime.state_machine import StateMachine


def test_valid_transitions_with_resume_paths():
    sm = StateMachine()
    sm.advance("explore")
    sm.advance("plan")
    sm.advance("implement")
    sm.advance("plan")
    sm.advance("implement")
    sm.advance("verify")
    sm.advance("review")
    sm.advance("report")
    assert sm.current == "report"
