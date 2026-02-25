def main():
    from app.models.model_loaders import get_threat_pipeline, get_attack_pipeline
    print("Hello from backend!")

    # Test model loading
    threat_pipeline = get_threat_pipeline()
    attack_pipeline = get_attack_pipeline()
    print(f"Threat Detection Pipeline: {threat_pipeline.random_state}")
    print(f"Attack Classification Pipeline: {attack_pipeline.random_state}")


if __name__ == "__main__":
    main()
