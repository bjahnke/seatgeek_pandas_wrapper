import math
import typing
from src.scalpyr.scalpyr import Scalpyr
import pandas as pd
import pydantic

# IdList is series or list of ids
IdList = typing.Union[pd.Series, typing.List[str]]


# pydantic class that represents events, performers, stats, and venue columns to be kept from the Seatgeek API
class SeatGeekDataStructure(pydantic.BaseModel):
    events: typing.List[str]
    performers: typing.List[str]
    stats: typing.List[str]
    venues: typing.List[str]


class ApiException(Exception):
    """thrown when an API request fails to give valid data"""


class ScalpyrPro(Scalpyr):
    """
    ScalpyrPro is a subclass of Scalpyr
    """

    def __init__(self, dev_key, sg_data_structure: SeatGeekDataStructure = None):
        super().__init__(dev_key)
        self.sg_data_structure = sg_data_structure
        if self.sg_data_structure is None:
            self.sg_data_structure = SeatGeekDataStructure(
                events=[
                    "type",
                    "id",
                    "datetime_utc",
                    "venue",
                    "performers",
                    "short_title",
                    "stats",
                    "url",
                    "score",
                    "announce_date",
                    "status",
                    "access_method",
                    "visible_at",
                ],
                performers=[
                    "type",
                    "name",
                    "id",
                    "has_upcoming_events",
                    "primary",
                    "url",
                    "score",
                    "slug",
                    "num_upcoming_events",
                ],
                stats=[
                    "listing_count",
                    "average_price",
                    "median_price",
                    "lowest_price",
                    "highest_price",
                ],
                venues=[
                    "state",
                    "postal_code",
                    "name",
                    "timezone",
                    "url",
                    "score",
                    "location",
                    "country",
                    "num_upcoming_events",
                    "city",
                    "slug",
                    "id",
                    "access_method",
                    "metro_code",
                    "capacity",
                ],
            )

    def _send_request(
        self, req_type=None, req_args=None, req_id=None
    ) -> typing.Tuple[pd.DataFrame, typing.Dict]:
        """
        Sends a request to the SeatGeek API and returns a dataframe of the response
        :param req_type:
        :param req_args:
        :param req_id:
        :return:
        """
        response = super()._send_request(req_type, req_args, req_id)
        # 'errors' in response keys, return response
        if req_type not in response.keys():
            raise ApiException(response)
        try:
            columns = getattr(self.sg_data_structure, req_type)

        except KeyError:
            raise ApiException(response)

        df = pd.DataFrame.from_dict(response[req_type])
        df = df[columns]
        response[req_type] = df
        return response

    def get_venue_ids(self, *venues: str) -> pd.DataFrame:
        """
        Get the venue ids for a list of venues
        :param venues:
        :return:
        """
        all_venue_data = []
        venue_search_failed = []
        for venue in venues:
            # account for multiple venues with the same name
            try:
                venue_data = self.get_venues({"name": venue})
            except ApiException as e:
                # venue not found
                venue_search_failed.append(venue)
                continue
            if len(venue_data.id) > 0:
                # with venue_data, create a dataframe with the search name, venue_data.name, and venue_data.id
                venue_data = venue_data.loc[venue_data.num_upcoming_events > 0].copy()
                venue_data_df = pd.DataFrame(
                    {"venue": venue_data.name, "venue_id": venue_data.id}
                )
                venue_data_df["searched_venue"] = venue
                all_venue_data.append(venue_data_df)
        if len(venue_search_failed) > 0:
            failed_search_str = "\n".join(venue_search_failed)
            print(f"Could not find venues: \n{failed_search_str}")
        # return a dataframe with the venue names and ids as columns
        return pd.concat(all_venue_data, ignore_index=True)

    def get_by_id(
        self, req_type: typing.Literal["events", "performers", "venues"], ids: IdList
    ) -> pd.DataFrame:
        """
        Returns a dataframe of events, performers, or venues for a given list of ids (respectively)
        :param req_type:
        :param ids:
        :return:
        """
        if isinstance(ids, pd.Series):
            ids = ",".join(ids.astype(str))
        else:
            ids = ",".join(ids)

        lookup = {
            "events": self.get_events,
            "performers": self.get_performers,
            "venues": self.get_venues,
        }
        return lookup[req_type]({"id": ids})

    def get_events_by(
        self,
        req_type: typing.Literal["performers", "venue", "events"],
        ids: IdList,
        per_page: int = 1000,
        event_type=None,
    ) -> pd.DataFrame:
        """
        Returns a dataframe of events for all given list of performer or venue ids.
        :param event_type:
        :param per_page:
        :param req_type:
        :param ids:
        :return:
        """

        if isinstance(ids, pd.Series):
            ids = ",".join(ids.astype(str))
        else:
            ids = ",".join(ids)
        if req_type == "events":
            lookup_field = "id"
        else:
            lookup_field = f"{req_type}.id"

        resp = self._get_events_by(
            lookup_field, ids, per_page, 1, event_type=event_type
        )
        total_records = resp["meta"]["total"]
        per_page = resp["meta"]["per_page"]
        total_pages = math.ceil(total_records / per_page)
        events_tables = [resp["events"]]
        page_num = 2
        while page_num <= total_pages:
            resp = self._get_events_by(
                lookup_field, ids, per_page, page_num, event_type=event_type
            )
            events_tables.append(resp["events"])
            page_num += 1

        resp["events"] = pd.concat(events_tables)
        return resp

    def _get_events_by(self, lookup_field, ids, per_page, page_num, event_type=None):
        """small helper for get_events_by"""
        req = dict() if event_type is None else {"type": event_type}
        req[lookup_field] = ids
        req["per_page"] = per_page
        req["page"] = page_num

        return self.get_events(req)
