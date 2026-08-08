import unittest

from postex.enums import WorkflowStage
from postex.errors import InvalidTransition
from postex.palette import Palette
from postex.workflow import PosterWorkflow


class WorkflowTests(unittest.TestCase):
    def test_required_approval_sequence(self) -> None:
        workflow = PosterWorkflow()
        with self.assertRaises(InvalidTransition):
            workflow.mark_rendered()

        workflow.request_cloud("openai", "paper.pdf", {"abstract": "text"})
        workflow.approve_cloud("owner")
        workflow.propose_deletions("d1", ["source-7"])
        workflow.approve_deletions("owner")
        workflow.palette.preview("p1", Palette(("#001122", "#AABBCC"), "image"))
        workflow.approve_palette("owner")
        self.assertIs(workflow.stage, WorkflowStage.READY_TO_RENDER)
        workflow.mark_rendered()
        workflow.mark_preflight_passed()
        self.assertIs(workflow.stage, WorkflowStage.PREFLIGHT_PASSED)


if __name__ == "__main__":
    unittest.main()
