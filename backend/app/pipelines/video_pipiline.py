class VideoPipelineService:
    """
    AI processing pipeline for uploaded videos.
    """

    def process(
        self,
        video_id: int,
        file_path: str,
    ):
        """
        Execute the complete AI pipeline.
        """
        self.extract_metadata(
            video_id,
            file_path,
        )
        # TODO
        # self.transcribe()
        # TODO
        # self.generate_summary()
        # TODO
        # self.create_embeddings()
        # TODO
        # self.translate()
        # TODO
        # self.generate_quiz()
        # TODO
        # self.generate_flashcards()
        
    def extract_metadata(
        self,
        video_id: int,
        file_path: str,
    ):
        print(
            f"[Pipeline] Extract metadata for {video_id}"
        )