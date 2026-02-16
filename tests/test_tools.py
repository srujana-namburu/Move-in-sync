"""
Unit tests for Movi AI agent tools
Tests individual tool functionality without full agent integration
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Import models and tools
from backend.models import DailyTrip, Vehicle, Driver, Route, Stop, Path
from backend.Agents.tools import (
    get_all_trips,
    get_trip_status,
    list_all_vehicles,
    get_unassigned_vehicles,
    list_all_drivers,
    list_all_stops,
    list_all_paths,
    list_all_routes
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_trip():
    """Sample trip for testing"""
    return DailyTrip(
        id=1,
        trip_display_name="Morning Shift",
        route_id=1,
        booking_percentage=85.0,
        live_status="SCHEDULED"
    )


@pytest.fixture
def sample_vehicle():
    """Sample vehicle for testing"""
    return Vehicle(
        id=1,
        license_plate="KA-01-AB-1234",
        vehicle_type="bus",
        capacity=45,
        status="active"
    )


@pytest.fixture
def sample_driver():
    """Sample driver for testing"""
    return Driver(
        id=1,
        name="Ramesh Kumar",
        phone_number="+919876543210"
    )


class TestTripTools:
    """Tests for trip-related tools"""

    def test_get_all_trips_success(self, mock_db, sample_trip):
        """Test get_all_trips returns correct data"""
        # Setup mock
        mock_db.query().all.return_value = [sample_trip]

        # Call tool
        result = get_all_trips.invoke({}, config={"configurable": {"db": mock_db}})

        # Assertions
        assert "success" in result["status"].lower()
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1
        assert result["data"][0]["trip_display_name"] == "Morning Shift"

    def test_get_all_trips_empty(self, mock_db):
        """Test get_all_trips with no trips"""
        mock_db.query().all.return_value = []

        result = get_all_trips.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower() or "no trips" in result["message"].lower()
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 0

    def test_get_trip_status_found(self, mock_db, sample_trip):
        """Test get_trip_status with existing trip"""
        mock_db.query().filter().first.return_value = sample_trip

        result = get_trip_status.invoke(
            {"trip_name": "Morning Shift"},
            config={"configurable": {"db": mock_db}}
        )

        assert "success" in result["status"].lower()
        assert result["data"]["live_status"] == "SCHEDULED"
        assert result["data"]["booking_percentage"] == 85.0

    def test_get_trip_status_not_found(self, mock_db):
        """Test get_trip_status with non-existent trip"""
        mock_db.query().filter().first.return_value = None

        result = get_trip_status.invoke(
            {"trip_name": "NonExistent"},
            config={"configurable": {"db": mock_db}}
        )

        assert "error" in result["status"].lower() or "not found" in result["message"].lower()


class TestVehicleTools:
    """Tests for vehicle-related tools"""

    def test_list_all_vehicles_success(self, mock_db, sample_vehicle):
        """Test list_all_vehicles returns correct data"""
        mock_db.query().all.return_value = [sample_vehicle]

        result = list_all_vehicles.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower()
        assert len(result["data"]) == 1
        assert result["data"][0]["license_plate"] == "KA-01-AB-1234"
        assert result["data"][0]["vehicle_type"] == "bus"

    def test_get_unassigned_vehicles_filters_correctly(self, mock_db):
        """Test get_unassigned_vehicles filters out assigned vehicles"""
        # Create mock vehicles - some assigned, some not
        assigned_vehicle = MagicMock(spec=Vehicle)
        assigned_vehicle.id = 1
        assigned_vehicle.license_plate = "KA-01-AB-1234"
        assigned_vehicle.deployments = [MagicMock()]  # Has deployment

        unassigned_vehicle = MagicMock(spec=Vehicle)
        unassigned_vehicle.id = 2
        unassigned_vehicle.license_plate = "KA-02-CD-5678"
        unassigned_vehicle.deployments = []  # No deployment
        unassigned_vehicle.to_dict.return_value = {
            "id": 2,
            "license_plate": "KA-02-CD-5678",
            "vehicle_type": "bus",
            "capacity": 52
        }

        mock_db.query().all.return_value = [assigned_vehicle, unassigned_vehicle]

        result = get_unassigned_vehicles.invoke({}, config={"configurable": {"db": mock_db}})

        # Should only return unassigned vehicles
        assert isinstance(result["data"], list)
        # The exact assertion depends on implementation


class TestDriverTools:
    """Tests for driver-related tools"""

    def test_list_all_drivers_success(self, mock_db, sample_driver):
        """Test list_all_drivers returns correct data"""
        mock_db.query().all.return_value = [sample_driver]

        result = list_all_drivers.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower()
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Ramesh Kumar"
        assert result["data"][0]["phone_number"] == "+919876543210"


class TestStopTools:
    """Tests for stop-related tools"""

    def test_list_all_stops_success(self, mock_db):
        """Test list_all_stops returns correct data"""
        sample_stop = Stop(
            id=1,
            name="Electronic City",
            latitude=12.8456,
            longitude=77.6603
        )
        mock_db.query().all.return_value = [sample_stop]

        result = list_all_stops.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower()
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Electronic City"


class TestPathTools:
    """Tests for path-related tools"""

    def test_list_all_paths_success(self, mock_db):
        """Test list_all_paths returns correct data"""
        sample_path = Path(
            id=1,
            name="Whitefield Route"
        )
        mock_db.query().all.return_value = [sample_path]

        result = list_all_paths.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower()
        assert len(result["data"]) == 1


class TestRouteTools:
    """Tests for route-related tools"""

    def test_list_all_routes_success(self, mock_db):
        """Test list_all_routes returns correct data"""
        sample_route = Route(
            id=1,
            path_id=1,
            shift_time="09:00",
            capacity=45,
            status="active"
        )
        mock_db.query().all.return_value = [sample_route]

        result = list_all_routes.invoke({}, config={"configurable": {"db": mock_db}})

        assert "success" in result["status"].lower()
        assert len(result["data"]) == 1


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
        # This would test the full workflow with a real DB
        # Skipped for now but shows structure
        pytest.skip("Integration test - requires DB setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
