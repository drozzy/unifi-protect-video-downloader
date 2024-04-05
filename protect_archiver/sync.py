import json
import logging
from typing import Optional
from datetime import datetime
from os import path
import dateutil.parser

from .client import ProtectClient
from .downloader import Downloader
from .utils import calculate_intervals
from .utils import json_encode


class ProtectSync:
    def __init__(self, client: ProtectClient, destination_path: str, statefile: str, start:Optional[datetime], end:Optional[datetime]) -> None:
        self.client = client
        self.start = start
        self.end = end
        self.statefile = path.abspath(path.join(destination_path, statefile))

    def readstate(self) -> dict:
        if path.isfile(self.statefile):
            with open(self.statefile) as fp:
                state = json.load(fp)
        else:
            state = {"cameras": {}}

        return state

    def writestate(self, state: dict) -> None:
        with open(self.statefile, "w") as fp:
            json.dump(state, fp, default=json_encode)


    def run(self, camera_list: list, ignore_state: bool = False) -> None:
        logging.info(f"Synchronizing video files from 'https://{self.client.address}:{self.client.port}'")

        if not ignore_state:
            state = self.readstate()
        else:
            state = {"cameras": {}}

        logging.info(f"State for the cameras found: {state}")

        if self.start:
            start_time = self.start
        else:
            # Find the earliest start date across all cameras
            start_time = datetime.now().replace(tzinfo=None)
            for camera in camera_list:
                camera_state = state["cameras"].setdefault(camera.id, {})
                camera_start = (
                        dateutil.parser.parse(camera_state["last"]).replace(
                            minute=0, second=0, microsecond=0
                        )
                        if "last" in camera_state
                        else camera.recording_start.replace(minute=0, second=0, microsecond=0)
                    )
                
                if camera_start < start_time:
                    start_time = camera_start

        curr_time = datetime.now().replace(minute=0, second=0, microsecond=0, tzinfo=None)
        end_time = self.end if self.end else curr_time

        for interval_start, interval_end in calculate_intervals(start_time, end_time):
            for camera in camera_list:
                camera_state = state["cameras"].get(camera.id, {})
                last_downloaded_str = camera_state.get("last", "1970-01-01T00:00:00")
                
                last_downloaded = dateutil.parser.parse(last_downloaded_str)
                last_downloaded = last_downloaded.replace(tzinfo=None, minute=0, second=0, microsecond=0)

                if interval_end > last_downloaded:
                    try:
                        Downloader.download_footage(
                            self.client,
                            interval_start,
                            interval_end,
                            camera,
                            disable_alignment=False,
                            disable_splitting=False,
                        )
                        state["cameras"][camera.id] = {
                            "last": interval_end.isoformat(),
                            "name": camera.name,
                        }
                        self.writestate(state)
                    except Exception:
                        logging.exception(f"Failed to sync camera {camera.name} - continuing to next device")