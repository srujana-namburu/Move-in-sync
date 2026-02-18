"""
Unit tests for Movi AI agent tools
Tests individual tool functionality without full agent integration
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.Agents.tools import (
    get_all_trips,
    get_trip_status,
    list_all_vehicles,
    get_unassigned_vehicles,
    list_all_drivers,
    list_all_stops,
    list_all_paths,
    list_all_routes,
)


class TestTripTools:
    """Tests for trip-related tools"""

    @patch("backend.Agents.tools.SessionLocal")
    def test_get_all_trips_success(self, mock_session_class):
        """Test get_all_trips returns trip names as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        trip = MagicMock()
        trip.display_name = "Morning Shift"
        mock_db.query.return_value.all.return_value = [trip]

        result = get_all_trips.invoke({})

        assert isinstance(result, str)
        assert "Morning Shift" in result

    @patch("backend.Agents.tools.SessionLocal")
    def test_get_all_trips_empty(self, mock_session_class):
        """Test get_all_trips with no trips"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = get_all_trips.invoke({})

        assert isinstance(result, str)
        assert "No trips found" in result

    @patch("backend.Agents.tools.SessionLocal")
    def test_get_trip_status_found(self, mock_session_class):
        """Test get_trip_status with an existing trip"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        trip = MagicMock()
        trip.trip_id = 1
        trip.display_name = "Morning Shift"
        trip.live_status = "SCHEDULED"
        trip.booking_status_percentage = 85.0

        # First filter().first() returns the trip; second (Deployment) returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [trip, None]

        result = get_trip_status.invoke({"trip_display_name": "Morning Shift"})

        assert isinstance(result, str)
        assert "Morning Shift" in result
        assert "SCHEDULED" in result

    @patch("backend.Agents.tools.SessionLocal")
    def test_get_trip_status_not_found(self, mock_session_class):
        """Test get_trip_status with non-existent trip"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_trip_status.invoke({"trip_display_name": "NonExistent"})

        assert isinstance(result, str)
        assert "not found" in result.lower()


class TestVehicleTools:
    """Tests for vehicle-related tools"""

    @patch("backend.Agents.tools.vehicle_crud")
    @patch("backend.Agents.tools.SessionLocal")
    def test_list_all_vehicles_success(self, mock_session_class, mock_vehicle_crud):
        """Test list_all_vehicles returns vehicle info as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        vehicle = MagicMock()
        vehicle.vehicle_id = 1
        vehicle.license_plate = "KA-01-AB-1234"
        vehicle.type.value = "bus"
        vehicle.capacity = 45
        vehicle.status = "active"
        mock_vehicle_crud.get_all_vehicles.return_value = [vehicle]

        result = list_all_vehicles.invoke({})

        assert isinstance(result, str)
        assert "KA-01-AB-1234" in result

    @patch("backend.Agents.tools.SessionLocal")
    def test_get_unassigned_vehicles_no_deployments(self, mock_session_class):
        """Test get_unassigned_vehicles when no vehicles are assigned"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # First query (Deployment).all() returns no deployments
        unassigned = MagicMock()
        unassigned.license_plate = "KA-02-CD-5678"

        def query_side_effect(model):
            q = MagicMock()
            from backend.models import Deployment
            if model is Deployment:
                q.all.return_value = []
            else:
                q.filter.return_value.all.return_value = [unassigned]
            return q

        mock_db.query.side_effect = query_side_effect

        result = get_unassigned_vehicles.invoke({})

        assert isinstance(result, str)
        assert "KA-02-CD-5678" in result


class TestDriverTools:
    """Tests for driver-related tools"""

    @patch("backend.Agents.tools.driver_crud")
    @patch("backend.Agents.tools.SessionLocal")
    def test_list_all_drivers_success(self, mock_session_class, mock_driver_crud):
        """Test list_all_drivers returns driver info as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        driver = MagicMock()
        driver.driver_id = 1
        driver.name = "Ramesh Kumar"
        driver.phone_number = "+919876543210"
        mock_driver_crud.get_all_drivers.return_value = [driver]

        result = list_all_drivers.invoke({})

        assert isinstance(result, str)
        assert "Ramesh Kumar" in result


class TestStopTools:
    """Tests for stop-related tools"""

    @patch("backend.Agents.tools.stop_crud")
    @patch("backend.Agents.tools.SessionLocal")
    def test_list_all_stops_success(self, mock_session_class, mock_stop_crud):
        """Test list_all_stops returns stop info as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        stop = MagicMock()
        stop.stop_id = 1
        stop.name = "Electronic City"
        stop.latitude = 12.8456
        stop.longitude = 77.6603
        mock_stop_crud.get_all_stops.return_value = [stop]

        result = list_all_stops.invoke({})

        assert isinstance(result, str)
        assert "Electronic City" in result


class TestPathTools:
    """Tests for path-related tools"""

    @patch("backend.Agents.tools.path_crud")
    @patch("backend.Agents.tools.SessionLocal")
    def test_list_all_paths_success(self, mock_session_class, mock_path_crud):
        """Test list_all_paths returns path info as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        path = MagicMock()
        path.path_id = 1
        path.path_name = "Whitefield Route"
        path.stops = []
        mock_path_crud.get_all_paths.return_value = [path]

        result = list_all_paths.invoke({})

        assert isinstance(result, str)
        assert "Whitefield Route" in result


class TestRouteTools:
    """Tests for route-related tools"""

    @patch("backend.Agents.tools.route_crud")
    @patch("backend.Agents.tools.SessionLocal")
    def test_list_all_routes_success(self, mock_session_class, mock_route_crud):
        """Test list_all_routes returns route info as a string"""
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        route = MagicMock()
        route.route_id = 1
        route.route_display_name = "Morning Route"
        route.path.path_name = "Whitefield Route"
        route.direction = "pickup"
        route.capacity = 45
        route.status.value = "active"
        mock_route_crud.get_all_routes.return_value = [route]

        result = list_all_routes.invoke({})

        assert isinstance(result, str)
        assert "Morning Route" in result


# Integration-style test (requires actual DB)
@pytest.mark.integration
class TestToolsIntegration:
    """Integration tests with actual database"""

    @pytest.fixture(scope="class")
    def test_db(self):
        """Create test database"""
        from backend.database import Base, engine
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)

    def test_full_tool_workflow(self, test_db):
        """Test complete workflow: create trip -> query trip -> update trip"""
        pytest.skip("Integration test - requires DB setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
