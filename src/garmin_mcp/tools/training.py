"""Training metrics tools (VO2max, training status, race predictions, etc.)."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import today_str
from garmin_mcp.sanitize import strip_pii


def register(mcp: FastMCP):
    @mcp.tool()
    def get_training_status(date: str = "") -> dict[str, Any]:
        """Get current training status (Productive, Maintaining, Overreaching,
        Detraining, Recovery, Peaking, Unproductive).

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()
        return client.get_training_status(d)

    @mcp.tool()
    def get_training_readiness(date: str = "") -> list[dict[str, Any]]:
        """Get training readiness score indicating how prepared you are
        for training today. Considers sleep, recovery, training load, and HRV.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()
        return strip_pii(client.get_training_readiness(d))

    @mcp.tool()
    def get_vo2max_and_fitness(date: str = "") -> dict[str, Any]:
        """Get VO2max estimate and fitness age data. Essential for
        Jack Daniels VDOT calculation and training pace zones.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
        """
        from garmin_mcp import get_client

        client = get_client()
        d = date or today_str()

        max_metrics = client.get_max_metrics(d)

        try:
            fitness_age = client.get_fitnessage_data(d)
        except Exception:
            fitness_age = None

        return {
            "max_metrics": max_metrics,
            "fitness_age": fitness_age,
        }

    @mcp.tool()
    def get_race_predictions() -> dict[str, Any]:
        """Get predicted race times for 5K, 10K, half marathon, and marathon
        based on current fitness level.
        """
        from garmin_mcp import get_client

        client = get_client()
        return client.get_race_predictions()

    @mcp.tool()
    def get_lactate_threshold(
        start_date: str = "",
        end_date: str = "",
    ) -> dict[str, Any]:
        """Get lactate threshold data. Critical for Norwegian double threshold
        training and zone-based training methods.

        Args:
            start_date: Start date (YYYY-MM-DD), optional
            end_date: End date (YYYY-MM-DD), optional
        """
        from garmin_mcp import get_client

        client = get_client()
        return strip_pii(client.get_lactate_threshold(
            start_date=start_date or None,
            end_date=end_date or None,
        ))
