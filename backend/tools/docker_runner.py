import docker
import os
import tempfile
import shutil

_base_image_built = False

def ensure_base_image(client, dockerfile_path: str):
    global _base_image_built

    if _base_image_built:
        return

    try:
        client.images.get("agent-base:latest")
        print("✅ Base image already exists")
        _base_image_built = True
        return
    except:
        pass

    print("🐳 Building base image (one time only)...")
    temp_dir = tempfile.mkdtemp()
    shutil.copy(dockerfile_path, os.path.join(temp_dir, "Dockerfile"))

    client.images.build(
        path=temp_dir,
        tag="agent-base:latest",
        rm=True,
        nocache=False
    )
    shutil.rmtree(temp_dir)
    print("✅ Base image ready")
    _base_image_built = True


def run_tests_in_docker(
    proposed_fix: dict[str, str],
    original_files: dict[str, str],
) -> dict:

    client = docker.from_env()
    temp_dir = None

    dockerfile_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../sandbox/Dockerfile"
        )
    )

    try:
        # Step 1 — Create temp directory
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp dir: {temp_dir}")

        # Step 2 — Write original files
        for file_path, content in original_files.items():
            filename = os.path.basename(file_path)
            full_path = os.path.join(temp_dir, filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📄 Written original: {filename}")

        # Step 3 — Overwrite with fixed files
        for file_path, content in proposed_fix.items():
            filename = os.path.basename(file_path)
            full_path = os.path.join(temp_dir, filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Written fix: {filename}")

        # Step 4 — Copy Dockerfile
        shutil.copy(
            dockerfile_path,
            os.path.join(temp_dir, "Dockerfile")
        )
        print("📄 Copied Dockerfile")

        # Step 5 — Ensure base image built once
        ensure_base_image(client, dockerfile_path)

        # Step 6 — Build test image
        print("🐳 Building test image...")
        image, _ = client.images.build(
            path=temp_dir,
            tag="agent-test:latest",
            rm=True,
            nocache=False
        )
        print("✅ Test image built")

        # Step 7 — Run container
        print("🚀 Running tests in Docker...")
        container = client.containers.run(
            "agent-test:latest",
            detach=True,
            stdout=True,
            stderr=True
        )

        result = container.wait()
        exit_code = result["StatusCode"]

        output = container.logs(
            stdout=True,
            stderr=True
        ).decode("utf-8")

        container.remove()

        print(f"📋 Exit code: {exit_code}")
        print(f"📋 Test output:\n{output}")

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