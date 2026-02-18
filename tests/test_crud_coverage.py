"""
CRUD coverage tests using an in-memory SQLite database.

Each test gets a fresh, isolated database so there are no ordering
dependencies or leftover state between tests.
"""
import sys
import os
import pytest
from datetime import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Stop, Path, PathStop, Route, Driver, Vehicle, DailyTrip, Deployment
from backend.schemas import (
    StopCreate,
    PathCreate,
    PathStopBase,
    RouteCreate,
    RouteStatus,
    VehicleType,
    DriverCreate,
    VehicleCreate,
    DailyTripCreate,
    DeploymentCreate,
)
from backend.crud import stop as stop_crud
from backend.crud import driver as driver_crud
from backend.crud import vehicle as vehicle_crud
from backend.crud import path as path_crud
from backend.crud import route as route_crud
from backend.crud import daily_trip as daily_trip_crud
from backend.crud import deployment as deployment_crud


# ---------------------------------------------------------------------------
# Shared fixture: fresh in-memory database per test
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helper: build a fully-wired hierarchy (stops → path → route → trip, vehicle, driver)
# ---------------------------------------------------------------------------

def _make_stops(db):
    s1 = Stop(name="Stop A", latitude=12.9, longitude=77.6)
    s2 = Stop(name="Stop B", latitude=12.8, longitude=77.5)
    db.add_all([s1, s2])
    db.flush()
    return s1, s2


def _make_path(db, s1, s2):
    p = Path(path_name="Test Path")
    db.add(p)
    db.flush()
    db.add(PathStop(path_id=p.path_id, stop_id=s1.stop_id, stop_order=1))
    db.add(PathStop(path_id=p.path_id, stop_id=s2.stop_id, stop_order=2))
    db.commit()
    db.refresh(p)
    return p


def _make_route(db, path):
    r = Route(
        path_id=path.path_id,
        route_display_name="Morning Route",
        shift_time=time(9, 0),
        direction="pickup",
        start_point="Stop A",
        end_point="Stop B",
        capacity=45,
        allocated_waitlist=0,
        status=RouteStatus.active,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _make_trip(db, route):
    t = DailyTrip(
        route_id=route.route_id,
        display_name="Morning Shift",
        booking_status_percentage=50.0,
        live_status="scheduled",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _make_vehicle(db):
    v = Vehicle(license_plate="KA-01-AA-1111", type=VehicleType.bus, capacity=45, status="active")
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _make_driver(db):
    d = Driver(name="Ramu", phone_number="+911234567890")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


# ===========================================================================
# STOP CRUD
# ===========================================================================

class TestStopCRUD:
    def test_create_and_get(self, db):
        s = stop_crud.create_stop(db, StopCreate(name="EC", latitude=12.9, longitude=77.6))
        assert s.stop_id is not None
        fetched = stop_crud.get_stop(db, s.stop_id)
        assert fetched.name == "EC"

    def test_get_by_name(self, db):
        stop_crud.create_stop(db, StopCreate(name="Koramangala", latitude=12.9, longitude=77.6))
        result = stop_crud.get_stop_by_name(db, "Koramangala")
        assert result is not None
        assert result.name == "Koramangala"

    def test_get_by_name_not_found(self, db):
        assert stop_crud.get_stop_by_name(db, "Ghost") is None

    def test_get_stops_pagination(self, db):
        for i in range(5):
            stop_crud.create_stop(db, StopCreate(name=f"Stop{i}", latitude=12.0, longitude=77.0))
        page = stop_crud.get_stops(db, skip=2, limit=2)
        assert len(page) == 2

    def test_get_all_stops(self, db):
        stop_crud.create_stop(db, StopCreate(name="X", latitude=1.0, longitude=1.0))
        stop_crud.create_stop(db, StopCreate(name="Y", latitude=2.0, longitude=2.0))
        all_stops = stop_crud.get_all_stops(db)
        assert len(all_stops) == 2

    def test_update_stop(self, db):
        s = stop_crud.create_stop(db, StopCreate(name="Old", latitude=1.0, longitude=1.0))
        updated = stop_crud.update_stop(db, s.stop_id, StopCreate(name="New", latitude=2.0, longitude=2.0))
        assert updated.name == "New"

    def test_update_stop_not_found(self, db):
        result = stop_crud.update_stop(db, 999, StopCreate(name="X", latitude=1.0, longitude=1.0))
        assert result is None

    def test_delete_stop(self, db):
        s = stop_crud.create_stop(db, StopCreate(name="Del", latitude=1.0, longitude=1.0))
        assert stop_crud.delete_stop(db, s.stop_id) is True
        assert stop_crud.get_stop(db, s.stop_id) is None

    def test_delete_stop_not_found(self, db):
        assert stop_crud.delete_stop(db, 999) is False

    def test_get_stop_count(self, db):
        stop_crud.create_stop(db, StopCreate(name="A", latitude=1.0, longitude=1.0))
        stop_crud.create_stop(db, StopCreate(name="B", latitude=2.0, longitude=2.0))
        assert stop_crud.get_stop_count(db) == 2

    def test_search_stops(self, db):
        stop_crud.create_stop(db, StopCreate(name="Electronic City", latitude=12.8, longitude=77.6))
        stop_crud.create_stop(db, StopCreate(name="Whitefield", latitude=12.9, longitude=77.7))
        results = stop_crud.search_stops(db, "electronic")
        assert len(results) == 1

    def test_get_stops_by_location(self, db):
        stop_crud.create_stop(db, StopCreate(name="InBox", latitude=12.5, longitude=77.5))
        stop_crud.create_stop(db, StopCreate(name="OutBox", latitude=15.0, longitude=80.0))
        results = stop_crud.get_stops_by_location(db, 12.0, 13.0, 77.0, 78.0)
        assert len(results) == 1
        assert results[0].name == "InBox"

    def test_check_stop_exists(self, db):
        s = stop_crud.create_stop(db, StopCreate(name="Check", latitude=1.0, longitude=1.0))
        assert stop_crud.check_stop_exists(db, s.stop_id) is True
        assert stop_crud.check_stop_exists(db, 999) is False

    def test_bulk_create_stops(self, db):
        stops = [
            StopCreate(name="Bulk1", latitude=1.0, longitude=1.0),
            StopCreate(name="Bulk2", latitude=2.0, longitude=2.0),
        ]
        created = stop_crud.bulk_create_stops(db, stops)
        assert len(created) == 2

    def test_get_stops_sorted_by_name(self, db):
        stop_crud.create_stop(db, StopCreate(name="Zeta", latitude=1.0, longitude=1.0))
        stop_crud.create_stop(db, StopCreate(name="Alpha", latitude=2.0, longitude=2.0))
        asc = stop_crud.get_stops_sorted_by_name(db, ascending=True)
        assert asc[0].name == "Alpha"
        desc = stop_crud.get_stops_sorted_by_name(db, ascending=False)
        assert desc[0].name == "Zeta"


# ===========================================================================
# DRIVER CRUD
# ===========================================================================

class TestDriverCRUD:
    def test_create_and_get(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="Raju", phone_number="+910000000001"))
        assert d.driver_id is not None
        fetched = driver_crud.get_driver(db, d.driver_id)
        assert fetched.name == "Raju"

    def test_get_driver_not_found(self, db):
        assert driver_crud.get_driver(db, 999) is None

    def test_get_by_phone(self, db):
        driver_crud.create_driver(db, DriverCreate(name="X", phone_number="+910000000002"))
        result = driver_crud.get_driver_by_phone(db, "+910000000002")
        assert result is not None

    def test_get_by_name(self, db):
        driver_crud.create_driver(db, DriverCreate(name="Unique", phone_number="+910000000003"))
        result = driver_crud.get_driver_by_name(db, "Unique")
        assert result is not None

    def test_get_drivers_pagination(self, db):
        for i in range(5):
            driver_crud.create_driver(db, DriverCreate(name=f"D{i}", phone_number=f"+91000000{i:04d}"))
        page = driver_crud.get_drivers(db, skip=1, limit=2)
        assert len(page) == 2

    def test_get_all_drivers(self, db):
        driver_crud.create_driver(db, DriverCreate(name="A", phone_number="+910000000010"))
        driver_crud.create_driver(db, DriverCreate(name="B", phone_number="+910000000011"))
        assert len(driver_crud.get_all_drivers(db)) == 2

    def test_get_available_drivers(self, db):
        driver_crud.create_driver(db, DriverCreate(name="Avail", phone_number="+910000000020"))
        result = driver_crud.get_available_drivers(db)
        assert len(result) >= 1

    def test_update_driver(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="Old", phone_number="+910000000030"))
        updated = driver_crud.update_driver(db, d.driver_id, DriverCreate(name="New", phone_number="+910000000031"))
        assert updated.name == "New"

    def test_update_driver_not_found(self, db):
        assert driver_crud.update_driver(db, 999, DriverCreate(name="X", phone_number="+910000000032")) is None

    def test_partial_update_driver(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="PartialOld", phone_number="+910000000040"))
        updated = driver_crud.partial_update_driver(db, d.driver_id, name="PartialNew")
        assert updated.name == "PartialNew"
        assert updated.phone_number == "+910000000040"

    def test_partial_update_driver_not_found(self, db):
        assert driver_crud.partial_update_driver(db, 999, name="X") is None

    def test_delete_driver(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="Del", phone_number="+910000000050"))
        assert driver_crud.delete_driver(db, d.driver_id) is True
        assert driver_crud.get_driver(db, d.driver_id) is None

    def test_delete_driver_not_found(self, db):
        assert driver_crud.delete_driver(db, 999) is False

    def test_get_driver_count(self, db):
        driver_crud.create_driver(db, DriverCreate(name="C1", phone_number="+910000000060"))
        driver_crud.create_driver(db, DriverCreate(name="C2", phone_number="+910000000061"))
        assert driver_crud.get_driver_count(db) == 2

    def test_search_drivers(self, db):
        driver_crud.create_driver(db, DriverCreate(name="Ramesh Kumar", phone_number="+910000000070"))
        driver_crud.create_driver(db, DriverCreate(name="Suresh", phone_number="+910000000071"))
        results = driver_crud.search_drivers(db, "ramesh")
        assert len(results) == 1

    def test_search_drivers_by_name(self, db):
        driver_crud.create_driver(db, DriverCreate(name="Mahesh", phone_number="+910000000080"))
        results = driver_crud.search_drivers_by_name(db, "mah")
        assert len(results) == 1

    def test_check_driver_exists(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="Exist", phone_number="+910000000090"))
        assert driver_crud.check_driver_exists(db, d.driver_id) is True
        assert driver_crud.check_driver_exists(db, 999) is False

    def test_check_phone_exists(self, db):
        d = driver_crud.create_driver(db, DriverCreate(name="Phone", phone_number="+910000000100"))
        assert driver_crud.check_phone_exists(db, "+910000000100") is True
        assert driver_crud.check_phone_exists(db, "+910000000100", exclude_driver_id=d.driver_id) is False
        assert driver_crud.check_phone_exists(db, "+919999999999") is False

    def test_bulk_create_drivers(self, db):
        drivers = [
            DriverCreate(name="B1", phone_number="+910000000110"),
            DriverCreate(name="B2", phone_number="+910000000111"),
        ]
        created = driver_crud.bulk_create_drivers(db, drivers)
        assert len(created) == 2

    def test_get_drivers_sorted_by_name(self, db):
        driver_crud.create_driver(db, DriverCreate(name="Zara", phone_number="+910000000120"))
        driver_crud.create_driver(db, DriverCreate(name="Aaron", phone_number="+910000000121"))
        asc = driver_crud.get_drivers_sorted_by_name(db, ascending=True)
        assert asc[0].name == "Aaron"
        desc = driver_crud.get_drivers_sorted_by_name(db, ascending=False)
        assert desc[0].name == "Zara"


# ===========================================================================
# VEHICLE CRUD
# ===========================================================================

class TestVehicleCRUD:
    def test_create_and_get(self, db):
        v = vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="KA-01-AB-0001", type=VehicleType.bus, capacity=45, status="active"))
        assert v.vehicle_id is not None
        fetched = vehicle_crud.get_vehicle(db, v.vehicle_id)
        assert fetched.license_plate == "KA-01-AB-0001"

    def test_get_vehicle_not_found(self, db):
        assert vehicle_crud.get_vehicle(db, 999) is None

    def test_get_by_license_plate(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="KA-01-AB-0002", type=VehicleType.cab, capacity=6, status="active"))
        result = vehicle_crud.get_vehicle_by_license_plate(db, "KA-01-AB-0002")
        assert result is not None

    def test_get_vehicles_pagination(self, db):
        for i in range(4):
            vehicle_crud.create_vehicle(db, VehicleCreate(
                license_plate=f"KA-01-AA-{i:04d}", type=VehicleType.bus, capacity=45, status="active"))
        page = vehicle_crud.get_vehicles(db, skip=1, limit=2)
        assert len(page) == 2

    def test_get_vehicles_by_type_filter(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="BUS-001", type=VehicleType.bus, capacity=45, status="active"))
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="CAB-001", type=VehicleType.cab, capacity=6, status="active"))
        buses = vehicle_crud.get_vehicles(db, vehicle_type=VehicleType.bus)
        assert all(v.type.value == VehicleType.bus.value for v in buses)

    def test_get_all_vehicles(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="ALL-001", type=VehicleType.bus, capacity=45, status="active"))
        assert len(vehicle_crud.get_all_vehicles(db)) >= 1

    def test_get_vehicles_by_type(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="TYPE-001", type=VehicleType.cab, capacity=6, status="active"))
        cabs = vehicle_crud.get_vehicles_by_type(db, VehicleType.cab)
        assert all(v.type.value == VehicleType.cab.value for v in cabs)

    def test_get_available_vehicles(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="AVAIL-001", type=VehicleType.bus, capacity=45, status="active"))
        result = vehicle_crud.get_available_vehicles(db)
        assert len(result) >= 1

    def test_get_available_vehicles_with_type_filter(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="AVAIL-CAB-001", type=VehicleType.cab, capacity=6, status="active"))
        result = vehicle_crud.get_available_vehicles(db, vehicle_type=VehicleType.cab)
        assert len(result) >= 1

    def test_update_vehicle(self, db):
        v = vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="UPD-001", type=VehicleType.bus, capacity=45, status="active"))
        updated = vehicle_crud.update_vehicle(db, v.vehicle_id, VehicleCreate(
            license_plate="UPD-001-NEW", type=VehicleType.bus, capacity=50, status="inactive"))
        assert updated.capacity == 50

    def test_update_vehicle_not_found(self, db):
        result = vehicle_crud.update_vehicle(db, 999, VehicleCreate(
            license_plate="X", type=VehicleType.bus, capacity=45, status="active"))
        assert result is None

    def test_delete_vehicle(self, db):
        v = vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="DEL-001", type=VehicleType.bus, capacity=45, status="active"))
        assert vehicle_crud.delete_vehicle(db, v.vehicle_id) is True
        assert vehicle_crud.get_vehicle(db, v.vehicle_id) is None

    def test_delete_vehicle_not_found(self, db):
        assert vehicle_crud.delete_vehicle(db, 999) is False

    def test_get_vehicle_count(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="CNT-001", type=VehicleType.bus, capacity=45, status="active"))
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="CNT-002", type=VehicleType.cab, capacity=6, status="active"))
        assert vehicle_crud.get_vehicle_count(db) == 2
        assert vehicle_crud.get_vehicle_count(db, VehicleType.bus) == 1

    def test_search_vehicles(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="SRCH-001", type=VehicleType.bus, capacity=45, status="active"))
        results = vehicle_crud.search_vehicles(db, "SRCH")
        assert len(results) == 1

    def test_get_vehicles_by_capacity_range(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="CAP-S-001", type=VehicleType.cab, capacity=6, status="active"))
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="CAP-L-001", type=VehicleType.bus, capacity=45, status="active"))
        small = vehicle_crud.get_vehicles_by_capacity_range(db, 1, 10)
        assert len(small) == 1
        assert small[0].capacity == 6

    def test_get_vehicles_by_status(self, db):
        vehicle_crud.create_vehicle(db, VehicleCreate(
            license_plate="STS-001", type=VehicleType.bus, capacity=45, status="inactive"))
        result = vehicle_crud.get_vehicles_by_status(db, "inactive")
        assert any(v.license_plate == "STS-001" for v in result)

    def test_bulk_create_vehicles(self, db):
        vehicles = [
            VehicleCreate(license_plate="BULK-001", type=VehicleType.bus, capacity=45, status="active"),
            VehicleCreate(license_plate="BULK-002", type=VehicleType.cab, capacity=6, status="active"),
        ]
        created = vehicle_crud.bulk_create_vehicles(db, vehicles)
        assert len(created) == 2


# ===========================================================================
# PATH CRUD
# ===========================================================================

class TestPathCRUD:
    def _create_stops(self, db):
        s1 = Stop(name="P-Stop-A", latitude=12.9, longitude=77.6)
        s2 = Stop(name="P-Stop-B", latitude=12.8, longitude=77.5)
        db.add_all([s1, s2])
        db.flush()
        return s1, s2

    def test_create_and_get_path(self, db):
        s1, s2 = self._create_stops(db)
        p = path_crud.create_path(db, PathCreate(
            path_name="Route P",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert p.path_id is not None
        fetched = path_crud.get_path(db, p.path_id)
        assert fetched.path_name == "Route P"

    def test_get_path_not_found(self, db):
        assert path_crud.get_path(db, 999) is None

    def test_get_path_by_name(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="Named Path",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        result = path_crud.get_path_by_name(db, "Named Path")
        assert result is not None

    def test_get_paths_pagination(self, db):
        s1, s2 = self._create_stops(db)
        for i in range(4):
            path_crud.create_path(db, PathCreate(
                path_name=f"Path{i}",
                stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                       PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        page = path_crud.get_paths(db, skip=1, limit=2)
        assert len(page) == 2

    def test_get_all_paths(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="AP1",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert len(path_crud.get_all_paths(db)) >= 1

    def test_update_path(self, db):
        s1, s2 = self._create_stops(db)
        p = path_crud.create_path(db, PathCreate(
            path_name="OldPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        updated = path_crud.update_path(db, p.path_id, PathCreate(
            path_name="NewPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert updated.path_name == "NewPath"

    def test_update_path_not_found(self, db):
        s1, s2 = self._create_stops(db)
        result = path_crud.update_path(db, 999, PathCreate(
            path_name="X",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert result is None

    def test_delete_path(self, db):
        s1, s2 = self._create_stops(db)
        p = path_crud.create_path(db, PathCreate(
            path_name="DeletePath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert path_crud.delete_path(db, p.path_id) is True

    def test_delete_path_not_found(self, db):
        assert path_crud.delete_path(db, 999) is False

    def test_get_path_count(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="CountPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert path_crud.get_path_count(db) >= 1

    def test_search_paths(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="Whitefield Express",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        results = path_crud.search_paths(db, "white")
        assert len(results) == 1

    def test_get_path_stops_ordered(self, db):
        s1, s2 = self._create_stops(db)
        p = path_crud.create_path(db, PathCreate(
            path_name="OrderPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        ordered = path_crud.get_path_stops_ordered(db, p.path_id)
        assert len(ordered) == 2

    def test_check_path_exists(self, db):
        s1, s2 = self._create_stops(db)
        p = path_crud.create_path(db, PathCreate(
            path_name="ExistsPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        assert path_crud.check_path_exists(db, p.path_id) is True
        assert path_crud.check_path_exists(db, 999) is False

    def test_get_paths_containing_stop(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="ContainsPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        results = path_crud.get_paths_containing_stop(db, s1.stop_id)
        assert len(results) >= 1

    def test_add_and_remove_stop_from_path(self, db):
        s1, s2 = self._create_stops(db)
        s3 = Stop(name="P-Stop-C", latitude=12.7, longitude=77.4)
        db.add(s3)
        db.flush()
        p = path_crud.create_path(db, PathCreate(
            path_name="ModPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        ps = path_crud.add_stop_to_path(db, p.path_id, s3.stop_id, 3)
        assert ps is not None
        removed = path_crud.remove_stop_from_path(db, p.path_id, s3.stop_id)
        assert removed is True

    def test_add_stop_to_nonexistent_path(self, db):
        s1, _ = self._create_stops(db)
        result = path_crud.add_stop_to_path(db, 999, s1.stop_id, 1)
        assert result is None

    def test_get_paths_sorted_by_name(self, db):
        s1, s2 = self._create_stops(db)
        path_crud.create_path(db, PathCreate(
            path_name="Zulu",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        path_crud.create_path(db, PathCreate(
            path_name="Alpha",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        asc = path_crud.get_paths_sorted_by_name(db, ascending=True)
        assert asc[0].path_name == "Alpha"
        desc = path_crud.get_paths_sorted_by_name(db, ascending=False)
        assert desc[0].path_name == "Zulu"


# ===========================================================================
# ROUTE CRUD
# ===========================================================================

class TestRouteCRUD:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        return p

    def test_create_and_get_route(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="R1",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        assert r.route_id is not None
        fetched = route_crud.get_route(db, r.route_id)
        assert fetched.route_display_name == "R1"

    def test_get_route_not_found(self, db):
        assert route_crud.get_route(db, 999) is None

    def test_create_route_invalid_path(self, db):
        with pytest.raises(ValueError):
            route_crud.create_route(db, RouteCreate(
                path_id=999, route_display_name="Bad",
                shift_time=time(9, 0), direction="pickup",
                capacity=45, allocated_waitlist=0, status=RouteStatus.active))

    def test_get_all_routes(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="GAll",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        routes = route_crud.get_all_routes(db)
        assert len(routes) >= 1

    def test_get_all_routes_filter_status(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Active",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        active = route_crud.get_all_routes(db, status=RouteStatus.active)
        assert all(r.status.value == RouteStatus.active.value for r in active)

    def test_get_routes_by_path(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="ByPath",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        results = route_crud.get_routes_by_path(db, p.path_id)
        assert len(results) >= 1

    def test_get_routes_by_status(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="ByStatus",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.deactivated))
        results = route_crud.get_routes_by_status(db, RouteStatus.deactivated)
        assert len(results) >= 1

    def test_get_routes_by_direction(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Drop",
            shift_time=time(18, 0), direction="drop",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        results = route_crud.get_routes_by_direction(db, "drop")
        assert len(results) >= 1

    def test_search_routes(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Whitefield Morning",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        results = route_crud.search_routes(db, "white")
        assert len(results) >= 1

    def test_get_routes_sorted_by_shift_time(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Late",
            shift_time=time(18, 0), direction="drop",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Early",
            shift_time=time(6, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        asc = route_crud.get_routes_sorted_by_shift_time(db, ascending=True)
        assert asc[0].shift_time <= asc[-1].shift_time
        desc = route_crud.get_routes_sorted_by_shift_time(db, ascending=False)
        assert desc[0].shift_time >= desc[-1].shift_time

    def test_get_route_count(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Cnt",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        assert route_crud.get_route_count(db) >= 1

    def test_check_route_exists(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="ChkExist",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        exists = route_crud.check_route_exists(db, p.path_id, time(9, 0), "pickup")
        assert exists is True
        not_exists = route_crud.check_route_exists(db, p.path_id, time(22, 0), "drop")
        assert not_exists is False

    def test_update_route_status(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="StatusUpdate",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.update_route_status(db, r.route_id, RouteStatus.deactivated)
        assert updated.status.value == RouteStatus.deactivated.value

    def test_update_route_status_not_found(self, db):
        assert route_crud.update_route_status(db, 999, RouteStatus.active) is None

    def test_update_route_capacity(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="CapUpdate",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.update_route_capacity(db, r.route_id, 60)
        assert updated.capacity == 60

    def test_update_route_capacity_not_found(self, db):
        assert route_crud.update_route_capacity(db, 999, 60) is None

    def test_update_route_waitlist(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="WaitUpdate",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.update_route_waitlist(db, r.route_id, 10)
        assert updated.allocated_waitlist == 10

    def test_update_route_waitlist_not_found(self, db):
        assert route_crud.update_route_waitlist(db, 999, 10) is None

    def test_delete_route(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="DelRoute",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        assert route_crud.delete_route(db, r.route_id) is True
        assert route_crud.get_route(db, r.route_id) is None

    def test_delete_route_not_found(self, db):
        assert route_crud.delete_route(db, 999) is False


# ===========================================================================
# DAILY TRIP CRUD
# ===========================================================================

class TestDailyTripCRUD:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        return r

    def test_create_and_get_trip(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Trip 1",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert t.trip_id is not None
        fetched = daily_trip_crud.get_daily_trip_by_id(db, t.trip_id)
        assert fetched.display_name == "Trip 1"

    def test_create_trip_invalid_route(self, db):
        with pytest.raises(ValueError):
            daily_trip_crud.create_daily_trip(db, DailyTripCreate(
                route_id=999, display_name="Bad Trip",
                booking_status_percentage=0.0, live_status="scheduled"))

    def test_get_trip_not_found(self, db):
        assert daily_trip_crud.get_daily_trip_by_id(db, 999) is None

    def test_get_trip_by_display_name(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Named Trip",
            booking_status_percentage=0.0, live_status="scheduled"))
        result = daily_trip_crud.get_daily_trip_by_display_name(db, "Named Trip")
        assert result is not None

    def test_get_all_daily_trips(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="All Trip",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert len(daily_trip_crud.get_all_daily_trips(db)) >= 1

    def test_get_daily_trips_by_route(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Route Trip",
            booking_status_percentage=0.0, live_status="scheduled"))
        results = daily_trip_crud.get_daily_trips_by_route(db, r.route_id)
        assert len(results) >= 1

    def test_get_daily_trips_by_live_status(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="InProgress",
            booking_status_percentage=50.0, live_status="in_progress"))
        results = daily_trip_crud.get_daily_trips_by_live_status(db, "in_progress")
        assert len(results) >= 1

    def test_update_booking_status(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="BookingTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        updated = daily_trip_crud.update_daily_trip_booking_status(db, t.trip_id, 75.0)
        assert updated.booking_status_percentage == 75.0

    def test_update_booking_status_not_found(self, db):
        assert daily_trip_crud.update_daily_trip_booking_status(db, 999, 50.0) is None

    def test_update_live_status(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="StatusTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        updated = daily_trip_crud.update_daily_trip_live_status(db, t.trip_id, "completed")
        assert updated.live_status == "completed"

    def test_update_live_status_not_found(self, db):
        assert daily_trip_crud.update_daily_trip_live_status(db, 999, "completed") is None

    def test_delete_trip(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="DelTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert daily_trip_crud.delete_daily_trip(db, t.trip_id) is True
        assert daily_trip_crud.get_daily_trip_by_id(db, t.trip_id) is None

    def test_delete_trip_not_found(self, db):
        assert daily_trip_crud.delete_daily_trip(db, 999) is False

    def test_check_trip_exists(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="ExistsTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert daily_trip_crud.check_daily_trip_exists(db, t.trip_id) is True
        assert daily_trip_crud.check_daily_trip_exists(db, 999) is False

    def test_get_total_count(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="CntTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert daily_trip_crud.get_total_daily_trips_count(db) >= 1

    def test_get_count_by_route(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="RCntTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert daily_trip_crud.get_daily_trips_count_by_route(db, r.route_id) >= 1

    def test_get_daily_trips_by_booking_range(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="RangeTrip",
            booking_status_percentage=80.0, live_status="scheduled"))
        results = daily_trip_crud.get_daily_trips_by_booking_range(db, 70.0, 100.0)
        assert len(results) >= 1

    def test_search_daily_trips_by_name(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Morning Express",
            booking_status_percentage=0.0, live_status="scheduled"))
        results = daily_trip_crud.search_daily_trips_by_name(db, "morning")
        assert len(results) >= 1

    def test_get_daily_trips_sorted(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Low",
            booking_status_percentage=10.0, live_status="scheduled"))
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="High",
            booking_status_percentage=90.0, live_status="scheduled"))
        desc = daily_trip_crud.get_daily_trips_sorted_by_booking_status(db, ascending=False)
        assert desc[0].booking_status_percentage >= desc[-1].booking_status_percentage
        asc = daily_trip_crud.get_daily_trips_sorted_by_booking_status(db, ascending=True)
        assert asc[0].booking_status_percentage <= asc[-1].booking_status_percentage

    def test_get_fully_booked_trips(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Full",
            booking_status_percentage=95.0, live_status="scheduled"))
        results = daily_trip_crud.get_fully_booked_trips(db, threshold=90.0)
        assert len(results) >= 1

    def test_get_available_trips(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Available",
            booking_status_percentage=20.0, live_status="scheduled"))
        results = daily_trip_crud.get_available_trips(db, threshold=50.0)
        assert len(results) >= 1


# ===========================================================================
# DEPLOYMENT CRUD
# ===========================================================================

class TestDeploymentCRUD:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        t = _make_trip(db, r)
        v = _make_vehicle(db)
        d = _make_driver(db)
        return t, v, d

    def test_create_and_get_deployment(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert dep.deployment_id is not None
        fetched = deployment_crud.get_deployment_by_id(db, dep.deployment_id)
        assert fetched.trip_id == t.trip_id

    def test_create_deployment_invalid_trip(self, db):
        _, v, d = self._setup(db)
        with pytest.raises(ValueError):
            deployment_crud.create_deployment(db, DeploymentCreate(
                trip_id=999, vehicle_id=v.vehicle_id, driver_id=d.driver_id))

    def test_create_deployment_invalid_vehicle(self, db):
        t, _, d = self._setup(db)
        with pytest.raises(ValueError):
            deployment_crud.create_deployment(db, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=999, driver_id=d.driver_id))

    def test_create_deployment_invalid_driver(self, db):
        t, v, _ = self._setup(db)
        with pytest.raises(ValueError):
            deployment_crud.create_deployment(db, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=999))

    def test_duplicate_vehicle_deployment(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        # Create a second driver with a unique phone number
        d2 = Driver(name="Ramu2", phone_number="+919999999999")
        db.add(d2)
        db.commit()
        db.refresh(d2)
        with pytest.raises(ValueError):
            deployment_crud.create_deployment(db, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d2.driver_id))

    def test_get_all_deployments(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        all_deps = deployment_crud.get_all_deployments(db)
        assert len(all_deps) >= 1

    def test_get_deployments_by_trip(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        results = deployment_crud.get_deployments_by_trip(db, t.trip_id)
        assert len(results) == 1

    def test_get_deployments_by_vehicle(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        results = deployment_crud.get_deployments_by_vehicle(db, v.vehicle_id)
        assert len(results) == 1

    def test_get_deployments_by_driver(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        results = deployment_crud.get_deployments_by_driver(db, d.driver_id)
        assert len(results) == 1

    def test_check_vehicle_availability(self, db):
        t, v, d = self._setup(db)
        assert deployment_crud.check_vehicle_availability(db, v.vehicle_id, t.trip_id) is True
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert deployment_crud.check_vehicle_availability(db, v.vehicle_id, t.trip_id) is False

    def test_check_driver_availability(self, db):
        t, v, d = self._setup(db)
        assert deployment_crud.check_driver_availability(db, d.driver_id, t.trip_id) is True
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert deployment_crud.check_driver_availability(db, d.driver_id, t.trip_id) is False

    def test_get_available_vehicles_for_trip(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        available = deployment_crud.get_available_vehicles_for_trip(db, t.trip_id)
        assert all(av.vehicle_id != v.vehicle_id for av in available)

    def test_get_available_drivers_for_trip(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        available = deployment_crud.get_available_drivers_for_trip(db, t.trip_id)
        assert all(av.driver_id != d.driver_id for av in available)

    def test_get_deployment_counts(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert deployment_crud.get_deployment_count_by_trip(db, t.trip_id) == 1
        assert deployment_crud.get_deployment_count_by_vehicle(db, v.vehicle_id) == 1
        assert deployment_crud.get_deployment_count_by_driver(db, d.driver_id) == 1
        assert deployment_crud.get_total_deployments_count(db) >= 1

    def test_check_deployment_exists(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert deployment_crud.check_deployment_exists(db, dep.deployment_id) is True
        assert deployment_crud.check_deployment_exists(db, 999) is False

    def test_delete_deployment(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert deployment_crud.delete_deployment(db, dep.deployment_id) is True
        assert deployment_crud.get_deployment_by_id(db, dep.deployment_id) is None

    def test_delete_deployment_not_found(self, db):
        assert deployment_crud.delete_deployment(db, 999) is False

    def test_delete_deployments_by_trip(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        count = deployment_crud.delete_deployments_by_trip(db, t.trip_id)
        assert count == 1

    def test_delete_deployments_by_vehicle(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        count = deployment_crud.delete_deployments_by_vehicle(db, v.vehicle_id)
        assert count == 1

    def test_delete_deployments_by_driver(self, db):
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        count = deployment_crud.delete_deployments_by_driver(db, d.driver_id)
        assert count == 1

    def test_get_deployment_by_trip_and_vehicle(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        found = deployment_crud.get_deployment_by_trip_and_vehicle(db, t.trip_id, v.vehicle_id)
        assert found is not None
        assert found.deployment_id == dep.deployment_id
        not_found = deployment_crud.get_deployment_by_trip_and_vehicle(db, t.trip_id, 999)
        assert not_found is None

    def test_get_deployment_by_trip_and_driver(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        found = deployment_crud.get_deployment_by_trip_and_driver(db, t.trip_id, d.driver_id)
        assert found is not None
        assert found.deployment_id == dep.deployment_id
        not_found = deployment_crud.get_deployment_by_trip_and_driver(db, t.trip_id, 999)
        assert not_found is None

    def test_create_bulk_deployments(self, db):
        t, v, d = self._setup(db)
        # Create second vehicle and driver for bulk
        v2 = Vehicle(license_plate="KA-02-ZZ-9999", type="cab", capacity=4, status="active")
        d2 = Driver(name="BulkDriver", phone_number="+910000000001")
        db.add_all([v2, d2])
        db.commit()
        db.refresh(v2)
        db.refresh(d2)
        # Use a second trip for the second deployment
        s1, s2 = _make_stops(db)
        p2 = _make_path(db, s1, s2)
        r2 = _make_route(db, p2)
        t2 = _make_trip(db, r2)
        results = deployment_crud.create_bulk_deployments(db, [
            DeploymentCreate(trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id),
            DeploymentCreate(trip_id=t2.trip_id, vehicle_id=v2.vehicle_id, driver_id=d2.driver_id),
        ])
        assert len(results) == 2

    def test_create_bulk_deployments_invalid_trip(self, db):
        _, v, d = self._setup(db)
        with pytest.raises(ValueError):
            deployment_crud.create_bulk_deployments(db, [
                DeploymentCreate(trip_id=999, vehicle_id=v.vehicle_id, driver_id=d.driver_id)
            ])

    def test_update_deployment(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        # Update with same values (no-op path)
        updated = deployment_crud.update_deployment(db, dep.deployment_id, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert updated is not None
        assert updated.deployment_id == dep.deployment_id

    def test_update_deployment_not_found(self, db):
        _, v, d = self._setup(db)
        result = deployment_crud.update_deployment(db, 999, DeploymentCreate(
            trip_id=1, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        assert result is None

    def test_update_deployment_vehicle(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        v2 = Vehicle(license_plate="KA-03-XX-1111", type="bus", capacity=50, status="active")
        db.add(v2)
        db.commit()
        db.refresh(v2)
        updated = deployment_crud.update_deployment_vehicle(db, dep.deployment_id, v2.vehicle_id)
        assert updated.vehicle_id == v2.vehicle_id

    def test_update_deployment_vehicle_not_found(self, db):
        result = deployment_crud.update_deployment_vehicle(db, 999, 1)
        assert result is None

    def test_update_deployment_vehicle_invalid_vehicle(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        with pytest.raises(ValueError):
            deployment_crud.update_deployment_vehicle(db, dep.deployment_id, 999)

    def test_update_deployment_driver(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        d2 = Driver(name="NewDriver", phone_number="+910000000002")
        db.add(d2)
        db.commit()
        db.refresh(d2)
        updated = deployment_crud.update_deployment_driver(db, dep.deployment_id, d2.driver_id)
        assert updated.driver_id == d2.driver_id

    def test_update_deployment_driver_not_found(self, db):
        result = deployment_crud.update_deployment_driver(db, 999, 1)
        assert result is None

    def test_update_deployment_driver_invalid_driver(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        with pytest.raises(ValueError):
            deployment_crud.update_deployment_driver(db, dep.deployment_id, 999)

    def test_bulk_delete_deployments(self, db):
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        dep_id = dep.deployment_id
        count = deployment_crud.bulk_delete_deployments(db, [dep_id])
        assert count == 1
        assert deployment_crud.get_deployment_by_id(db, dep_id) is None

    def test_bulk_delete_deployments_empty(self, db):
        count = deployment_crud.bulk_delete_deployments(db, [999, 998])
        assert count == 0


# ===========================================================================
# ADDITIONAL ROUTE CRUD (bulk/update/range coverage)
# ===========================================================================

class TestRouteCRUDBulk:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        return p

    def test_update_route(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Original",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.update_route(db, r.route_id, RouteCreate(
            path_id=p.path_id, route_display_name="Updated",
            shift_time=time(10, 0), direction="drop",
            capacity=50, allocated_waitlist=5, status=RouteStatus.deactivated))
        assert updated.route_display_name == "Updated"
        assert updated.capacity == 50

    def test_update_route_not_found(self, db):
        result = route_crud.update_route(db, 999, RouteCreate(
            path_id=1, route_display_name="X",
            shift_time=time(9, 0), direction="pickup",
            capacity=10, allocated_waitlist=0, status=RouteStatus.active))
        assert result is None

    def test_update_route_invalid_path(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="ToFail",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        with pytest.raises(ValueError):
            route_crud.update_route(db, r.route_id, RouteCreate(
                path_id=999, route_display_name="X",
                shift_time=time(9, 0), direction="pickup",
                capacity=10, allocated_waitlist=0, status=RouteStatus.active))

    def test_update_route_with_new_path(self, db):
        s1, s2 = _make_stops(db)
        p1 = _make_path(db, s1, s2)
        s3 = Stop(name="NewStop-A", latitude=13.0, longitude=77.5)
        s4 = Stop(name="NewStop-B", latitude=13.1, longitude=77.6)
        db.add_all([s3, s4])
        db.flush()
        p2 = path_crud.create_path(db, PathCreate(
            path_name="NewPath",
            stops=[PathStopBase(stop_id=s3.stop_id, stop_order=1),
                   PathStopBase(stop_id=s4.stop_id, stop_order=2)]))
        r = route_crud.create_route(db, RouteCreate(
            path_id=p1.path_id, route_display_name="SwitchPath",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.update_route(db, r.route_id, RouteCreate(
            path_id=p2.path_id, route_display_name="SwitchPath",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        assert updated.path_id == p2.path_id
        assert updated.start_point == "NewStop-A"

    def test_partial_update_route(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Partial",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.partial_update_route(db, r.route_id, {"capacity": 99})
        assert updated.capacity == 99
        assert updated.route_display_name == "Partial"

    def test_partial_update_route_not_found(self, db):
        result = route_crud.partial_update_route(db, 999, {"capacity": 10})
        assert result is None

    def test_partial_update_route_with_path_change(self, db):
        s1, s2 = _make_stops(db)
        p1 = _make_path(db, s1, s2)
        s3 = Stop(name="PartStop-A", latitude=13.2, longitude=77.7)
        s4 = Stop(name="PartStop-B", latitude=13.3, longitude=77.8)
        db.add_all([s3, s4])
        db.flush()
        p2 = path_crud.create_path(db, PathCreate(
            path_name="PartPath",
            stops=[PathStopBase(stop_id=s3.stop_id, stop_order=1),
                   PathStopBase(stop_id=s4.stop_id, stop_order=2)]))
        r = route_crud.create_route(db, RouteCreate(
            path_id=p1.path_id, route_display_name="PartialPath",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        updated = route_crud.partial_update_route(db, r.route_id, {"path_id": p2.path_id})
        assert updated.path_id == p2.path_id
        assert updated.start_point == "PartStop-A"

    def test_partial_update_invalid_path(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="BadPartial",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        with pytest.raises(ValueError):
            route_crud.partial_update_route(db, r.route_id, {"path_id": 999})

    def test_delete_routes_by_path(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="PathDel1",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="PathDel2",
            shift_time=time(18, 0), direction="drop",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        count = route_crud.delete_routes_by_path(db, p.path_id)
        assert count == 2
        assert len(route_crud.get_routes_by_path(db, p.path_id)) == 0

    def test_bulk_create_routes(self, db):
        p = self._setup(db)
        routes = route_crud.bulk_create_routes(db, [
            RouteCreate(path_id=p.path_id, route_display_name="Bulk1",
                        shift_time=time(8, 0), direction="pickup",
                        capacity=45, allocated_waitlist=0, status=RouteStatus.active),
            RouteCreate(path_id=p.path_id, route_display_name="Bulk2",
                        shift_time=time(20, 0), direction="drop",
                        capacity=30, allocated_waitlist=2, status=RouteStatus.active),
        ])
        assert len(routes) == 2
        assert routes[0].route_display_name == "Bulk1"
        assert routes[1].route_display_name == "Bulk2"

    def test_bulk_create_routes_invalid_path(self, db):
        with pytest.raises(ValueError):
            route_crud.bulk_create_routes(db, [
                RouteCreate(path_id=999, route_display_name="Bad",
                            shift_time=time(8, 0), direction="pickup",
                            capacity=45, allocated_waitlist=0, status=RouteStatus.active)
            ])

    def test_bulk_update_route_status(self, db):
        p = self._setup(db)
        r1 = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="BulkSt1",
            shift_time=time(7, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        r2 = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="BulkSt2",
            shift_time=time(19, 0), direction="drop",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        count = route_crud.bulk_update_route_status(
            db, [r1.route_id, r2.route_id], RouteStatus.deactivated)
        assert count == 2

    def test_get_routes_by_shift_time_range(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Morning",
            shift_time=time(8, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="Evening",
            shift_time=time(18, 0), direction="drop",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        results = route_crud.get_routes_by_shift_time_range(db, time(7, 0), time(10, 0))
        assert len(results) >= 1
        names = [r.route_display_name for r in results]
        assert "Morning" in names
        assert "Evening" not in names

    def test_check_route_exists_with_exclude(self, db):
        p = self._setup(db)
        r = route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="ExcludeMe",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        # Should return False when excluding its own ID
        exists = route_crud.check_route_exists(
            db, p.path_id, time(9, 0), "pickup", exclude_route_id=r.route_id)
        assert exists is False
        # Should return True without exclusion
        exists_no_excl = route_crud.check_route_exists(db, p.path_id, time(9, 0), "pickup")
        assert exists_no_excl is True

    def test_get_route_count_by_status(self, db):
        p = self._setup(db)
        route_crud.create_route(db, RouteCreate(
            path_id=p.path_id, route_display_name="CntActive",
            shift_time=time(9, 0), direction="pickup",
            capacity=45, allocated_waitlist=0, status=RouteStatus.active))
        count = route_crud.get_route_count(db, status=RouteStatus.active)
        assert count >= 1


# ===========================================================================
# ADDITIONAL DAILY TRIP CRUD (bulk/update/delete coverage)
# ===========================================================================

class TestDailyTripCRUDBulk:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        return r

    def test_create_bulk_daily_trips(self, db):
        r = self._setup(db)
        trips = daily_trip_crud.create_bulk_daily_trips(db, [
            DailyTripCreate(route_id=r.route_id, display_name="Bulk Trip 1",
                            booking_status_percentage=0.0, live_status="scheduled"),
            DailyTripCreate(route_id=r.route_id, display_name="Bulk Trip 2",
                            booking_status_percentage=50.0, live_status="in_progress"),
        ])
        assert len(trips) == 2
        assert trips[0].display_name == "Bulk Trip 1"

    def test_create_bulk_daily_trips_invalid_route(self, db):
        with pytest.raises(ValueError):
            daily_trip_crud.create_bulk_daily_trips(db, [
                DailyTripCreate(route_id=999, display_name="Bad",
                                booking_status_percentage=0.0, live_status="scheduled")
            ])

    def test_update_daily_trip(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="UpdTrip",
            booking_status_percentage=0.0, live_status="scheduled"))
        updated = daily_trip_crud.update_daily_trip(db, t.trip_id, DailyTripCreate(
            route_id=r.route_id, display_name="UpdTrip Modified",
            booking_status_percentage=60.0, live_status="in_progress"))
        assert updated.display_name == "UpdTrip Modified"
        assert updated.booking_status_percentage == 60.0
        assert updated.live_status == "in_progress"

    def test_update_daily_trip_not_found(self, db):
        r = self._setup(db)
        result = daily_trip_crud.update_daily_trip(db, 999, DailyTripCreate(
            route_id=r.route_id, display_name="X",
            booking_status_percentage=0.0, live_status="scheduled"))
        assert result is None

    def test_update_daily_trip_invalid_route(self, db):
        r = self._setup(db)
        t = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="UpdBad",
            booking_status_percentage=0.0, live_status="scheduled"))
        with pytest.raises(ValueError):
            daily_trip_crud.update_daily_trip(db, t.trip_id, DailyTripCreate(
                route_id=999, display_name="UpdBad",
                booking_status_percentage=0.0, live_status="scheduled"))

    def test_bulk_update_live_status(self, db):
        r = self._setup(db)
        t1 = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="BulkSt1",
            booking_status_percentage=0.0, live_status="scheduled"))
        t2 = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="BulkSt2",
            booking_status_percentage=0.0, live_status="scheduled"))
        count = daily_trip_crud.bulk_update_live_status(
            db, [t1.trip_id, t2.trip_id], "completed")
        assert count == 2

    def test_delete_daily_trips_by_route(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="ByRoute1",
            booking_status_percentage=0.0, live_status="scheduled"))
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="ByRoute2",
            booking_status_percentage=0.0, live_status="scheduled"))
        count = daily_trip_crud.delete_daily_trips_by_route(db, r.route_id)
        assert count == 2
        assert len(daily_trip_crud.get_daily_trips_by_route(db, r.route_id)) == 0

    def test_delete_daily_trips_by_status(self, db):
        r = self._setup(db)
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Cancelled1",
            booking_status_percentage=0.0, live_status="cancelled"))
        daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="Cancelled2",
            booking_status_percentage=0.0, live_status="cancelled"))
        count = daily_trip_crud.delete_daily_trips_by_status(db, "cancelled")
        assert count == 2
        assert len(daily_trip_crud.get_daily_trips_by_live_status(db, "cancelled")) == 0

    def test_bulk_delete_daily_trips(self, db):
        r = self._setup(db)
        t1 = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="BulkDel1",
            booking_status_percentage=0.0, live_status="scheduled"))
        t2 = daily_trip_crud.create_daily_trip(db, DailyTripCreate(
            route_id=r.route_id, display_name="BulkDel2",
            booking_status_percentage=0.0, live_status="scheduled"))
        t1_id, t2_id = t1.trip_id, t2.trip_id
        count = daily_trip_crud.bulk_delete_daily_trips(db, [t1_id, t2_id])
        assert count == 2
        assert daily_trip_crud.get_daily_trip_by_id(db, t1_id) is None
        assert daily_trip_crud.get_daily_trip_by_id(db, t2_id) is None

    def test_bulk_delete_daily_trips_empty(self, db):
        count = daily_trip_crud.bulk_delete_daily_trips(db, [999, 998])
        assert count == 0


# ===========================================================================
# EDGE CASE COVERAGE (deployment conflicts, path stop count, driver phone)
# ===========================================================================

class TestDeploymentEdgeCases:
    def _setup(self, db):
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        t = _make_trip(db, r)
        v = _make_vehicle(db)
        d = _make_driver(db)
        return t, v, d

    def test_duplicate_driver_deployment(self, db):
        """Cover line 51 in deployment.py - duplicate driver in same trip."""
        t, v, d = self._setup(db)
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        v2 = Vehicle(license_plate="KA-99-YY-0001", type="cab", capacity=4, status="active")
        db.add(v2)
        db.commit()
        db.refresh(v2)
        with pytest.raises(ValueError, match="already deployed"):
            deployment_crud.create_deployment(db, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=v2.vehicle_id, driver_id=d.driver_id))

    def test_create_bulk_deployments_invalid_vehicle(self, db):
        """Cover line 77 in deployment.py - invalid vehicle in bulk create."""
        t, _, d = self._setup(db)
        with pytest.raises(ValueError, match="Vehicle with id 999"):
            deployment_crud.create_bulk_deployments(db, [
                DeploymentCreate(trip_id=t.trip_id, vehicle_id=999, driver_id=d.driver_id)
            ])

    def test_create_bulk_deployments_invalid_driver(self, db):
        """Cover line 81 in deployment.py - invalid driver in bulk create."""
        t, v, _ = self._setup(db)
        with pytest.raises(ValueError, match="Driver with id 999"):
            deployment_crud.create_bulk_deployments(db, [
                DeploymentCreate(trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=999)
            ])

    def test_update_deployment_vehicle_conflict(self, db):
        """Cover line 355 in deployment.py - vehicle already deployed to same trip."""
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        t = _make_trip(db, r)
        v1 = _make_vehicle(db)
        d1 = _make_driver(db)
        d2 = Driver(name="DriverConflict", phone_number="+910000000010")
        v2 = Vehicle(license_plate="KA-99-CC-0002", type="bus", capacity=50, status="active")
        db.add_all([d2, v2])
        db.commit()
        db.refresh(d2)
        db.refresh(v2)
        dep1 = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v1.vehicle_id, driver_id=d1.driver_id))
        # Deploy v2 to same trip with d2
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v2.vehicle_id, driver_id=d2.driver_id))
        # Try to update dep1's vehicle to v2 (already deployed to this trip)
        with pytest.raises(ValueError, match="already deployed"):
            deployment_crud.update_deployment_vehicle(db, dep1.deployment_id, v2.vehicle_id)

    def test_update_deployment_driver_conflict(self, db):
        """Cover line 391 in deployment.py - driver already deployed to same trip."""
        s1, s2 = _make_stops(db)
        p = _make_path(db, s1, s2)
        r = _make_route(db, p)
        t = _make_trip(db, r)
        v1 = _make_vehicle(db)
        d1 = _make_driver(db)
        d2 = Driver(name="DriverConflict2", phone_number="+910000000011")
        v2 = Vehicle(license_plate="KA-99-DD-0003", type="bus", capacity=50, status="active")
        db.add_all([d2, v2])
        db.commit()
        db.refresh(d2)
        db.refresh(v2)
        dep1 = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v1.vehicle_id, driver_id=d1.driver_id))
        deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v2.vehicle_id, driver_id=d2.driver_id))
        # Try to update dep1's driver to d2 (already deployed to this trip)
        with pytest.raises(ValueError, match="already deployed"):
            deployment_crud.update_deployment_driver(db, dep1.deployment_id, d2.driver_id)

    def test_update_deployment_with_changed_vehicle_invalid(self, db):
        """Cover lines 286-299 in deployment.py - invalid vehicle in update_deployment."""
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        v2 = Vehicle(license_plate="KA-99-EE-0004", type="cab", capacity=4, status="active")
        db.add(v2)
        db.commit()
        db.refresh(v2)
        # Use a different vehicle_id that doesn't exist
        with pytest.raises(ValueError, match="Vehicle with id 999"):
            deployment_crud.update_deployment(db, dep.deployment_id, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=999, driver_id=d.driver_id))

    def test_update_deployment_with_changed_driver_invalid(self, db):
        """Cover lines 303-316 in deployment.py - invalid driver in update_deployment."""
        t, v, d = self._setup(db)
        dep = deployment_crud.create_deployment(db, DeploymentCreate(
            trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=d.driver_id))
        with pytest.raises(ValueError, match="Driver with id 999"):
            deployment_crud.update_deployment(db, dep.deployment_id, DeploymentCreate(
                trip_id=t.trip_id, vehicle_id=v.vehicle_id, driver_id=999))


class TestPathStopCount:
    def test_get_paths_by_stop_count(self, db):
        """Cover lines 264-276 in path.py - get_paths_by_stop_count."""
        s1, s2 = _make_stops(db)
        s3 = Stop(name="StopCount-C", latitude=13.5, longitude=78.0)
        db.add(s3)
        db.flush()
        # Path with 2 stops
        path_crud.create_path(db, PathCreate(
            path_name="TwoStopPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2)]))
        # Path with 3 stops
        path_crud.create_path(db, PathCreate(
            path_name="ThreeStopPath",
            stops=[PathStopBase(stop_id=s1.stop_id, stop_order=1),
                   PathStopBase(stop_id=s2.stop_id, stop_order=2),
                   PathStopBase(stop_id=s3.stop_id, stop_order=3)]))
        results = path_crud.get_paths_by_stop_count(db, min_stops=2, max_stops=2)
        assert all(len(path_crud.get_path(db, r.path_id).stops) == 2 for r in results)
        results_min = path_crud.get_paths_by_stop_count(db, min_stops=3)
        assert len(results_min) >= 1


class TestDriverPhoneUpdate:
    def test_update_driver_phone(self, db):
        """Cover line 159 in driver.py - updating phone number via partial_update_driver."""
        d = _make_driver(db)
        from crud.driver import partial_update_driver
        updated = partial_update_driver(db, d.driver_id, phone_number="+910000000099")
        assert updated.phone_number == "+910000000099"
