from dataclasses import dataclass

from plugins.damage_types._base import DamageTypeBase


@dataclass
class Generic(DamageTypeBase):
    """Neutral element with no strengths or weaknesses.

    Serves as the baseline damage type focused on consistent damage without
    side effects.
    """
    id: str = "Generic"
    weakness: str = "none"
    color: tuple[int, int, int] = (255, 255, 255)

    async def ultimate(self, actor, allies, enemies):
        """Split the user's attack into 64 rapid strikes on one target.

        Deprecated wrapper routed through the Generic ultimate action.
        """

        from plugins.actions.ultimate.generic_ultimate import GenericUltimate
        from plugins.actions.ultimate.utils import run_ultimate_action

        result = await run_ultimate_action(GenericUltimate, actor, allies, enemies)
        return bool(getattr(result, "success", False))

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Splits the user's attack into 64 rapid strikes on a single target, "
            "counting each hit as a separate action. The strike cadence follows "
            "TURN_PACING via the battle pacing helper."
        )
