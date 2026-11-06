import pandas as pd
import time
import os
from dotenv import load_dotenv
from entsoe import EntsoePandasClient
import time


def get_entsoe_data(ENTSOE_API_TOKEN, zone_a, zone_b):
    start_time = time.perf_counter()

    api_key = ENTSOE_API_TOKEN

    if not api_key:
        raise ValueError("from get_entsoe_data(): ENTSOE_API_TOKEN not found in .env")

    client = EntsoePandasClient(api_key=api_key)

    # Last 2 years
    end = pd.Timestamp.now(tz="Europe/Brussels").normalize()
    start = end - pd.DateOffset(years=2)
    split = start + pd.DateOffset(years=1)

    periods = [(start, split), (split, end)]

    results = []

    for period_start, period_end in periods:
        for source, destination in [
            (zone_a, zone_b),
            (zone_b, zone_a),
        ]:
            try:
                flow = client.query_crossborder_flows(
                    source,
                    destination,
                    start=period_start,
                    end=period_end,
                )

                if not flow.empty:
                    temp = flow.rename("flow_MW").to_frame()
                    temp.index.name = "timestamp"
                    temp["from_zone"] = source
                    temp["to_zone"] = destination
                    results.append(temp.reset_index())
                    # ensure we did get rows
                    print(f"Retrieved {source} -> {destination}, {len(flow)} rows")
                # pause between aech api call for 0.2 seconds, to not overwhelm api
                time.sleep(0.2)

            except Exception as e:
                print(f"Failed {source} -> {destination}")
                print("Error type:", type(e).__name__)
                print("Error details:", repr(e))

    if results:
        flows_df = pd.concat(results, ignore_index=True)
        flows_df = flows_df[["timestamp", "from_zone", "to_zone", "flow_MW"]]
        flows_df = flows_df.sort_values("timestamp").reset_index(drop=True)
    else:
        flows_df = pd.DataFrame(
            columns=["timestamp", "from_zone", "to_zone", "flow_MW"]
        )

    print(flows_df.head())
    print(f"Rows retrieved: {len(flows_df)}")

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"Total retrieval time: {elapsed:.2f} seconds")
    print(f"Total retrieval time: {elapsed / 60:.2f} minutes")
    return flows_df
