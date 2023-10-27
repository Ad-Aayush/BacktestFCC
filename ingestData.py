from zipline.data.bundles import register, ingest
from zipline.data.bundles.csvdir import csvdir_equities

# Define the bundle registration and ingest function
csv_directory = './Data'  # Update this path
bundle_name = 'my_custom_bundle'
register(
    bundle_name,
    csvdir_equities(
        ['daily'],
        csv_directory,
    ),
    calendar_name='XBOM'
)

if __name__ == '__main__':
    # Ingest the data
    ingest(bundle_name, show_progress=True)
