from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    Member,
    Skill,
    SkillCreate,
    Team,
    TeamCreate,
    Upload,
    UploadStatus,
)
from app.tests.api.routes.test_skills import valid_tool_definition
from app.tests.utils.utils import random_lower_string


def create_team(db: Session, user_id: int) -> Team:
    team_data = {
        "name": random_lower_string(),
        "description": None,
        "workflow": "sequential",  # assuming a valid workflow
        "owner_id": user_id,
    }
    team = Team.model_validate(TeamCreate(**team_data), update={"owner_id": user_id})
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def test_read_teams(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_team(db, 1)
    response = client.get(
        f"{settings.API_V1_STR}/teams", headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "data" in data


def test_read_team(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team = create_team(db, 1)
    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == team.name


def test_create_team(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team_data = {
        "name": random_lower_string(),
        "description": random_lower_string(),
        "workflow": "sequential",
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams", json=team_data, headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == team_data["name"]
    assert data["description"] == team_data["description"]


def test_export_team(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team = create_team(db, 1)
    skill = Skill.model_validate(
        SkillCreate(
            name=random_lower_string(),
            description=random_lower_string(),
            tool_definition=valid_tool_definition,
        ),
        update={"owner_id": 1},
    )
    upload = Upload(
        name=random_lower_string(),
        description=random_lower_string(),
        owner_id=1,
        status=UploadStatus.COMPLETED,
    )
    member = Member(
        name=random_lower_string(),
        role="Answer questions",
        type="freelancer_root",
        owner_of=None,
        position_x=10,
        position_y=20,
        source=None,
        belongs_to=team.id,
    )
    member.skills = [skill]
    member.uploads = [upload]
    db.add(skill)
    db.add(upload)
    db.add(member)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}/export",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == team.name
    assert data["workflow"] == team.workflow
    assert any(item["name"] == member.name for item in data["members"])
    exported_member = next(
        item for item in data["members"] if item["name"] == member.name
    )
    assert exported_member["skills"][0]["name"] == skill.name
    assert exported_member["uploads"][0]["name"] == upload.name


def test_import_team_recreates_graph_and_drops_missing_references(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    existing_skill = Skill.model_validate(
        SkillCreate(
            name=random_lower_string(),
            description=random_lower_string(),
            tool_definition=valid_tool_definition,
        ),
        update={"owner_id": 1},
    )
    existing_upload = Upload(
        name=random_lower_string(),
        description=random_lower_string(),
        owner_id=1,
        status=UploadStatus.COMPLETED,
    )
    db.add(existing_skill)
    db.add(existing_upload)
    db.commit()

    team_export = {
        "export_version": 1,
        "id": 77,
        "name": random_lower_string(),
        "description": "Imported team",
        "workflow": "hierarchical",
        "members": [
            {
                "id": 1,
                "name": "Leader",
                "role": "Lead",
                "type": "root",
                "owner_of": 77,
                "position_x": 0,
                "position_y": 0,
                "source": None,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "interrupt": False,
                "base_url": None,
                "skills": [
                    {"name": existing_skill.name},
                    {"name": "missing skill"},
                ],
                "uploads": [
                    {"name": existing_upload.name},
                    {"name": "missing upload"},
                ],
            },
            {
                "id": 2,
                "name": "Worker",
                "role": "Work",
                "type": "worker",
                "owner_of": 1,
                "position_x": 100,
                "position_y": 200,
                "source": 1,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "interrupt": True,
                "base_url": None,
                "skills": [],
                "uploads": [],
            },
        ],
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/import",
        json=team_export,
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == team_export["name"]

    imported_team = db.get(Team, data["id"])
    assert imported_team is not None
    imported_members = {member.name: member for member in imported_team.members}
    assert imported_members["Leader"].owner_of == imported_team.id
    assert imported_members["Worker"].source == imported_members["Leader"].id
    assert imported_members["Worker"].owner_of == imported_members["Leader"].id
    assert [skill.name for skill in imported_members["Leader"].skills] == [
        existing_skill.name
    ]
    assert [upload.name for upload in imported_members["Leader"].uploads] == [
        existing_upload.name
    ]


def test_create_team_duplicate_name(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team = create_team(db, 1)
    duplicate_team_data = {
        "name": team.name,
        "description": random_lower_string(),
        "workflow": "sequential",
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams",
        json=duplicate_team_data,
        headers=superuser_token_headers,
    )
    assert response.status_code == 400


def test_update_team(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team = create_team(db, 1)
    updated_team_data = {"name": random_lower_string()}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=updated_team_data,
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == updated_team_data["name"]


def test_delete_team(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    team = create_team(db, 1)
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
