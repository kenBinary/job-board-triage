from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.common.enums.job_board import JobBoardEnum
from src.facebook_posts.models.facebook_post_link import FacebookPostLink
from src.indeed.models.indeed_link import IndeedLink
from src.jobstreet.models.jobstreet_link import JobStreetLink
from src.kalibrr.models.kalibrr_link import KalibrrLink
from src.linkedin.models.linkedin_link import LinkedInLink
from src.linkedin_posts.models.linkedin_post_link import LinkedInPostLink
from src.mynimo.models.mynimo_link import MynimoLink
from src.olj.models.olj_link import OljLink

_CONFIG_FILE = Path("config.json")


def _parse_links(raw: Any, from_dict_fn: Any) -> list | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError(f"Expected a list, got {type(raw).__name__!r}.")
    return [from_dict_fn(item) if isinstance(item, dict) else item for item in raw]


class ScrapersConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    indeed: list[IndeedLink] | None = None
    jobstreet: list[JobStreetLink] | None = None
    kalibrr: list[KalibrrLink] | None = None
    linkedin: list[LinkedInLink] | None = None
    linkedin_posts: list[LinkedInPostLink] | None = Field(
        default=None, alias="linkedin-posts"
    )
    mynimo: list[MynimoLink] | None = None
    olj: list[OljLink] | None = None
    facebook_posts: list[FacebookPostLink] | None = Field(
        default=None, alias="facebook-posts"
    )

    @field_validator("indeed", mode="before")
    @classmethod
    def parse_indeed(cls, v: Any) -> Any:
        return _parse_links(v, IndeedLink.from_dict)

    @field_validator("jobstreet", mode="before")
    @classmethod
    def parse_jobstreet(cls, v: Any) -> Any:
        return _parse_links(v, JobStreetLink.from_dict)

    @field_validator("kalibrr", mode="before")
    @classmethod
    def parse_kalibrr(cls, v: Any) -> Any:
        return _parse_links(v, KalibrrLink.from_dict)

    @field_validator("linkedin", mode="before")
    @classmethod
    def parse_linkedin(cls, v: Any) -> Any:
        return _parse_links(v, LinkedInLink.from_dict)

    @field_validator("linkedin_posts", mode="before")
    @classmethod
    def parse_linkedin_posts(cls, v: Any) -> Any:
        return _parse_links(v, LinkedInPostLink.from_dict)

    @field_validator("mynimo", mode="before")
    @classmethod
    def parse_mynimo(cls, v: Any) -> Any:
        return _parse_links(v, MynimoLink.from_dict)

    @field_validator("olj", mode="before")
    @classmethod
    def parse_olj(cls, v: Any) -> Any:
        return _parse_links(v, OljLink.from_dict)

    @field_validator("facebook_posts", mode="before")
    @classmethod
    def parse_facebook_posts(cls, v: Any) -> Any:
        return _parse_links(v, FacebookPostLink.from_dict)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        json_file="config.json",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    scrapers: ScrapersConfig = Field(default_factory=ScrapersConfig)
    max_consecutive_link_errors: int = 3

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    def get_scraper_links(self, board: JobBoardEnum) -> list[Any]:
        """Return configured links for the given board.

        Raises:
            FileNotFoundError: If config.json does not exist.
            ValueError: If the board has no links configured in config.json.
        """
        if not _CONFIG_FILE.exists():
            raise FileNotFoundError(
                "config.json not found. "
                "Copy config.json.template to config.json and populate it with your scraper links."
            )

        board_attr_map: dict[JobBoardEnum, list[Any] | None] = {
            JobBoardEnum.Indeed: self.scrapers.indeed,
            JobBoardEnum.JobStreet: self.scrapers.jobstreet,
            JobBoardEnum.Kalibrr: self.scrapers.kalibrr,
            JobBoardEnum.Linkedin: self.scrapers.linkedin,
            JobBoardEnum.LinkedinPosts: self.scrapers.linkedin_posts,
            JobBoardEnum.Mynimo: self.scrapers.mynimo,
            JobBoardEnum.Olj: self.scrapers.olj,
            JobBoardEnum.FacebookPosts: self.scrapers.facebook_posts,
        }

        links = board_attr_map.get(board)
        if not links:
            raise ValueError(
                f"No link configuration found for '{board.value}' in config.json. "
                f"Please add links for '{board.value}' under the 'scrapers' key in config.json "
                f"(see config.json.template for reference)."
            )
        return links


def _load_settings() -> Settings:
    if not _CONFIG_FILE.exists():
        raise FileNotFoundError(
            "config.json not found. "
            "Copy config.json.template to config.json and populate it with your scraper links."
        )
    return Settings()


settings = _load_settings()
