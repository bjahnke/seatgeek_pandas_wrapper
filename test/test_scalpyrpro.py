import pytest
import pandas as pd
import src.scalpyr.scalpyrpro as scalpyrpro
import env


@pytest.fixture
def sg_client():
    client = scalpyrpro.ScalpyrPro(env.SEATGEEK_CLIENT_ID)
    return client


def test_get_venue_ids(sg_client):
    client = sg_client
    # real venue names to search
    venue_names = [
        "Madison Square Garden",
        "Barclays Center",
        "TD Garden",
        "Staples Center",
        "Oracle Arena",
    ]
    # real venue ids to compare to
    venue_ids = [100, 101, 102, 103, 104]
    # get venue ids
    venue_ids_test = client.get_venue_ids(*venue_names)
    # compare venue ids
    assert venue_ids_test == venue_ids


def test_scalpyrpro_get_events_by(sg_client):
    """
    test get_events_by method
    :param sg_client:
    :return:
    """
    performer_data = sg_client.get_performers({"id": "2351"})
    res = sg_client.get_events_by(req_type="performers", ids=["2351"])
    res = sg_client.get_events_by(
        req_type="venue",
        ids=[
            "100",
            "101",
            "102",
            "103",
            "104",
            "105",
            "106",
            "107",
            "108",
            "109",
            "110",
            "111",
            "112",
            "113",
        ],
        event_type="concert",
    )
    assert res["meta"]["total"] == len(res["events"])
    print("done")
