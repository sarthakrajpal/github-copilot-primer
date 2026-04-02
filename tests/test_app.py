from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)
original_activities = deepcopy(app_module.activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: Save current state before test
    yield
    # Assert (teardown): restore global state to avoid cross-test contamination
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))


def test_root_redirect():
    # Arrange
    # (client fixture is already arranged)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert "/static/index.html" in response.headers.get("location", "")


def test_get_activities():
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_for_existing_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    assert email not in app_module.activities[activity_name]["participants"]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "ghost.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_registered():
    # Arrange
    activity_name = "Chess Club"
    existing_email = app_module.activities[activity_name]["participants"][0]

    # Act
    first_response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert
    assert first_response.status_code == 400
    assert first_response.json()["detail"] == "Student already signed up"


def test_unregister_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]
    assert email in app_module.activities[activity_name]["participants"]

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_not_registered():
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_unregister_nonexistent_activity():
    # Arrange
    activity_name = "Fake Club"
    email = "x.student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
