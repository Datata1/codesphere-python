import argparse
import asyncio

from codesphere import CodesphereSDK


async def delete_all_workspaces(team_id: int, dry_run: bool = False) -> None:
    async with CodesphereSDK() as sdk:
        print(f"Fetching workspaces for team {team_id}...")
        workspaces = await sdk.workspaces.list(team_id=team_id)

        if not workspaces:
            print("No workspaces found in this team.")
            return

        print(f"Found {len(workspaces)} workspace(s):\n")
        for ws in workspaces:
            print(f"  • {ws.name} (ID: {ws.id})")

        if dry_run:
            print("\n[DRY RUN] No workspaces were deleted.")
            return

        print("\n" + "=" * 50)
        confirm = input(f"Delete all {len(workspaces)} workspaces? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        print("\nDeleting workspaces...")
        for ws in workspaces:
            try:
                await ws.delete()
                print(f"  ✓ Deleted: {ws.name} (ID: {ws.id})")
            except Exception as e:
                print(f"  ✗ Failed to delete {ws.name}: {e}")

        print(f"\n✓ Done. Deleted {len(workspaces)} workspace(s).")


def main():
    parser = argparse.ArgumentParser(description="Delete all workspaces in a team")
    parser.add_argument("--team-id", type=int, required=True, help="Team ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    args = parser.parse_args()

    asyncio.run(delete_all_workspaces(team_id=args.team_id, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
