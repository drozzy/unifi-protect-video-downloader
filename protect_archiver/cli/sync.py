from os import path

import click
from typing import Optional
from datetime import datetime

from protect_archiver.cli.base import cli
from protect_archiver.client import ProtectClient
from protect_archiver.config import Config
from protect_archiver.sync import ProtectSync
from protect_archiver.utils import print_download_stats


@cli.command("sync", help="Synchronize your UniFi Protect footage to a local destination")
@click.argument("dest", type=click.Path(exists=True, writable=True, resolve_path=True))
@click.option(
    "--address",
    default=Config.ADDRESS,
    show_default=True,
    required=True,
    help="IP address or hostname of the UniFi Protect Server",
    envvar="PROTECT_ADDRESS",
    show_envvar=True,
)
@click.option(
    "--max-usage",
    default=80,
    help='Percent of disk space that must remain free before downloading a file',
)
@click.option(
    "--port",
    default=Config.PORT,
    show_default=True,
    required=False,
    help="The port of the UniFi Protect Server",
    envvar="PROTECT_PORT",
    show_envvar=True,
)
@click.option(
    "--not-unifi-os",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use this for systems without UniFi OS",
    envvar="PROTECT_NOT_UNIFI_OS",
    show_envvar=True,
)
@click.option(
    "--username",
    required=True,
    help="Username of user with local access",
    prompt="Username of local Protect user",
    envvar="PROTECT_USERNAME",
    show_envvar=True,
)
@click.option(
    "--password",
    required=True,
    help="Password of user with local access",
    prompt="Password for local Protect user",
    hide_input=True,
    envvar="PROTECT_PASSWORD",
    show_envvar=True,
)
@click.option(
    "--verify-ssl",
    is_flag=True,
    default=False,
    show_default=True,
    help="Verify Protect SSL certificate",
    envvar="PROTECT_VERIFY_SSL",
    show_envvar=True,
)
@click.option(
    "--cameras",
    default="all",
    show_default=True,
    help=(
        "Comma-separated list of one or more camera IDs ('--cameras=\"id_1,id_2,id_3,...\"'). "
        "Use '--cameras=all' to download footage of all available cameras."
    ),
    envvar="PROTECT_CAMERAS",
    show_envvar=True,
)
@click.option(
    "--wait-between-downloads",
    "download_wait",
    default=0,
    show_default=True,
    help="Time to wait between file downloads, in seconds",
    envvar="PROTECT_WAIT_BETWEEN_DOWNLOADS",
    show_envvar=True,
)
@click.option(
    "--ignore-failed-downloads",
    is_flag=True,
    default=False,
    show_default=True,
    help="Ignore failed downloads and continue with next download",
    envvar="PROTECT_IGNORE_FAILED_DOWNLOADS",
    show_envvar=True,
)
@click.option(
    "--skip-existing-files",
    is_flag=True,
    default=False,
    show_default=True,
    help="Skip downloading files which already exist on disk",
    envvar="PROTECT_SKIP_EXISTING",
    show_envvar=True,
)
@click.option(
    "--use-utc-filenames",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use UTC timestamp in file names instead of local time",
    envvar="PROTECT_USE_UTC",
    show_envvar=True,
)
@click.option(
    "--statefile",
    default="sync.state",
    show_default=True,
    envvar="PROTECT_SYNC_STATEFILE",
    show_envvar=True,
)
@click.option(
    "--ignore-state",
    is_flag=True,
    default=False,
    show_default=True,
    envvar="PROTECT_SYNC_IGNORE_STATE",
    show_envvar=True,
)
@click.option(
    "--start",
    type=click.DateTime(
        formats=[
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
        ]
    ),
    required=False,
    help=(
        "Sync range start time. "
    )
)
@click.option(
    "--end",
    type=click.DateTime(
        formats=[
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
        ]
    ),
    required=False,
    help=(
        "Sync range end time. "
    )
)
def sync(
    dest: str,
    address: str,
    max_usage:int,
    port: int,
    not_unifi_os: bool,
    username: str,
    password: str,
    verify_ssl: bool,
    statefile: str,
    ignore_state: bool,
    ignore_failed_downloads: bool,
    download_wait: int,
    skip_existing_files: bool,
    cameras: str,
    use_utc_filenames: bool,
    start:Optional[datetime],
    end:Optional[datetime]
) -> None:
    # normalize path to destination directory and check if it exists
    dest = path.abspath(dest)
    if not path.isdir(dest):
        click.echo(f"Video file destination directory '{dest} is invalid or does not exist!")
        exit(1)

    client = ProtectClient(
        address=address,
        max_usage=max_usage,
        port=port,
        not_unifi_os=not_unifi_os,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        destination_path=dest,
        ignore_failed_downloads=ignore_failed_downloads,
        download_wait=download_wait,
        skip_existing_files=skip_existing_files,
        use_subfolders=True,
        use_utc_filenames=use_utc_filenames,
    )

    # get camera list
    print("Getting camera list")
    camera_list = client.get_camera_list()

    if cameras != "all":
        camera_ids = set(cameras.split(","))
        camera_list = [c for c in camera_list if c.id in camera_ids]

    process = ProtectSync(client=client, destination_path=dest, statefile=statefile, start=start, end=end)
    process.run(camera_list, ignore_state=ignore_state)

    print_download_stats(client)
