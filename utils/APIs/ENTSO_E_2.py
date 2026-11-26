import pandas as pd
import time
from entsoe import EntsoePandasClient


def get_entsoe_data(api_token, zone_a, zone_b, from_date, to_date):

    start_time = time.perf_counter()

    if not api_token:
        raise ValueError("ENTSOE API token not provided.")

    client = EntsoePandasClient(api_key=api_token)

    # Convert dates to timezone-aware timestamps
    start = pd.Timestamp(from_date, tz="Europe/Brussels")
    end = pd.Timestamp(to_date, tz="Europe/Brussels")

    results = []

    for source, destination in [
        (zone_a, zone_b),
        (zone_b, zone_a),
    ]:
        try:
            flow = client.query_crossborder_flows(
                source,
                destination,
                start=start,
                end=end,
            )

            if not flow.empty:
                temp = flow.rename("flow_MW").to_frame()
                temp.index.name = "timestamp"
                temp["from_zone"] = source
                temp["to_zone"] = destination

                results.append(temp.reset_index())

                print(f"Retrieved {source} -> {destination}: {len(flow)} rows")

            time.sleep(0.2)

        except Exception as e:
            print(f"Failed {source} -> {destination}")
            print("Error:", repr(e))

    if results:
        flows_df = pd.concat(results, ignore_index=True)

        # Resample hourly data to weekly averages
        weekly_df = (
            flows_df.set_index("timestamp")
            .groupby(["from_zone", "to_zone"])["flow_MW"]
            .resample("W-MON")
            .mean()
            .reset_index()
        )

        weekly_df = weekly_df.sort_values("timestamp").reset_index(drop=True)

    else:
        weekly_df = pd.DataFrame(
            columns=["timestamp", "from_zone", "to_zone", "flow_MW"]
        )

    print(weekly_df.head())
    print(f"Rows retrieved: {len(weekly_df)}")

    elapsed = time.perf_counter() - start_time
    print(f"Total retrieval time: {elapsed:.2f} seconds")

    return weekly_df
