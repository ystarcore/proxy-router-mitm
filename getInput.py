import argparse


def get_arguments():
    parser = argparse.ArgumentParser(description="Parameter Options")

    parser.add_argument(
        "-i",
        "--local-ip",
        default="127.0.0.1",
        help="Local Ip address for mitm proxy server (default=127.0.0.1)",
    )
    parser.add_argument(
        "-p",
        "--local-port",
        default="8081",
        help="Local Port for mitm proxy server (default=8081)",
    )

    args = parser.parse_args()

    return (
        args.local_ip,
        args.local_port,
    )
