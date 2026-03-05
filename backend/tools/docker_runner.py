import docker
import os
import tempfile
import shutil

def run_tests_in_docker(
    proposed_fix: dict[str, str],
    original_files: dict[str, str],
    test_command: list[str] = ["pytest", ".", "-v"]
) -> dict:

    client = docker.from_env()
    temp_dir = None

    try:
        # Step 1 — Create temp directory
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp dir: {temp_dir}")

        # Step 2 — Write original files
        for file_path, content in original_files.items():
            filename = os.path.basename(file_path)
            full_path = os.path.join(temp_dir, filename)
            with open(full_path, "w") as f:
                f.write(content)
            print(f"📄 Written original: {filename}")

        # Step 3 — Overwrite with fixed files
        for file_path, content in proposed_fix.items():
            filename = os.path.basename(file_path)
            full_path = os.path.join(temp_dir, filename)
            with open(full_path, "w") as f:
                f.write(content)
            print(f"✅ Written fix: {filename}")

        # Step 4 — Copy Dockerfile
        dockerfile_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../../sandbox/Dockerfile"
            )
        )
        shutil.copy(dockerfile_path, temp_dir)
        print("📄 Copied Dockerfile")

        # Step 5 — Build Docker image
        print("🐳 Building Docker image...")
        image, build_logs = client.images.build(
            path=temp_dir,
            tag="agent-test:latest",
            rm=True
        )
        print("✅ Docker image built")

        # Step 6 — Run container
        # KEY FIX: dont use remove=True
        # instead manually remove after reading logs
        print("🚀 Running tests in Docker...")
        container = client.containers.run(
            "agent-test:latest",
            command=test_command,
            detach=True,        # run in background
            stdout=True,
            stderr=True
        )

        # Wait for container to finish
        result = container.wait()
        exit_code = result["StatusCode"]

        # Get ALL logs including errors
        output = container.logs(
            stdout=True,
            stderr=True
        ).decode("utf-8")

        # Now remove container
        container.remove()

        print(f"📋 Exit code: {exit_code}")
        print(f"📋 Test output:\n{output}")

        # passed = exit code 0
        passed = exit_code == 0

        return {
            "passed": passed,
            "output": output
        }

    except Exception as e:
        print(f"❌ Docker error: {e}")
        return {
            "passed": False,
            "output": str(e)
        }

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up temp dir")
