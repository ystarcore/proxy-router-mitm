# ----------------------------------
# proxy - main.py
# @author Carl
# @since October 17, 2024 11:08 PM
# ----------------------------------
from getInput import get_arguments
from mitmproxy.tools.main import mitmdump


# Start the proxy server
if __name__ == "__main__":
    (local_ip, local_port) = get_arguments()

    mitmdump(
        [
            "--ssl-insecure",
            "--mode",
            "regular",
            "--showhost",
            "--set",
            "block_global=false",
            "--listen-host",
            local_ip,
            "-p",
            local_port,
            "-s",
            f"KeywordProxy.py",
        ]
    )
