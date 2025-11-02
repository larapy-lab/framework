from typing import Optional, List, Callable, Any, Dict


class SlackAttachment:
    def __init__(self):
        self.title_text = None
        self.title_url = None
        self.content_text = None
        self.fallback_text = None
        self.color_value = "good"
        self.attachment_fields = []
        self.markdown_in = []
        self.author_name = None
        self.author_link = None
        self.author_icon = None
        self.image_url_value = None
        self.thumb_url_value = None
        self.footer_text = None
        self.footer_icon = None
        self.timestamp_value = None

    def title(self, title: str, url: Optional[str] = None):
        self.title_text = title
        if url:
            self.title_url = url
        return self

    def content(self, content: str):
        self.content_text = content
        return self

    def fallback(self, fallback: str):
        self.fallback_text = fallback
        return self

    def color(self, color: str):
        self.color_value = color
        return self

    def field(self, title: str, content: str, short: bool = True):
        self.attachment_fields.append({"title": title, "value": content, "short": short})
        return self

    def fields(self, fields: List[dict]):
        self.attachment_fields.extend(fields)
        return self

    def markdown(self, fields: List[str]):
        self.markdown_in = fields
        return self

    def author(self, name: str, link: Optional[str] = None, icon: Optional[str] = None):
        self.author_name = name
        if link:
            self.author_link = link
        if icon:
            self.author_icon = icon
        return self

    def image(self, url: str):
        self.image_url_value = url
        return self

    def thumb(self, url: str):
        self.thumb_url_value = url
        return self

    def footer_info(self, footer: str, icon: Optional[str] = None):
        self.footer_text = footer
        if icon:
            self.footer_icon = icon
        return self

    def timestamp(self, timestamp: int):
        self.timestamp_value = timestamp
        return self

    def to_dict(self) -> dict:
        attachment = {
            "fallback": self.fallback_text or self.content_text,
            "color": self.color_value,
        }

        if self.title_text:
            attachment["title"] = self.title_text
        if self.title_url:
            attachment["title_link"] = self.title_url
        if self.content_text:
            attachment["text"] = self.content_text
        if self.attachment_fields:
            attachment["fields"] = self.attachment_fields
        if self.markdown_in:
            attachment["mrkdwn_in"] = self.markdown_in
        if self.author_name:
            attachment["author_name"] = self.author_name
        if self.author_link:
            attachment["author_link"] = self.author_link
        if self.author_icon:
            attachment["author_icon"] = self.author_icon
        if self.image_url_value:
            attachment["image_url"] = self.image_url_value
        if self.thumb_url_value:
            attachment["thumb_url"] = self.thumb_url_value
        if self.footer_text:
            attachment["footer"] = self.footer_text
        if self.footer_icon:
            attachment["footer_icon"] = self.footer_icon
        if self.timestamp_value:
            attachment["ts"] = self.timestamp_value

        return attachment


class SlackMessage:
    def __init__(self):
        self.level = "info"
        self.username_value = None
        self.icon_value = None
        self.image_url_value = None
        self.channel_value = None
        self.content_text = None
        self.attachment_list = []
        self.http_options = {}

    def success(self):
        self.level = "success"
        return self

    def error(self):
        self.level = "error"
        return self

    def warning(self):
        self.level = "warning"
        return self

    def info(self):
        self.level = "info"
        return self

    def from_user(self, username: str, icon: Optional[str] = None):
        self.username_value = username
        if icon:
            self.icon_value = icon
        return self

    def username(self, username: str):
        self.username_value = username
        return self

    def icon(self, icon: str):
        self.icon_value = icon
        return self

    def image(self, url: str):
        self.image_url_value = url
        return self

    def to(self, channel: str):
        self.channel_value = channel
        return self

    def content(self, content: str):
        self.content_text = content
        return self

    def attachment(self, callback: Callable[[SlackAttachment], SlackAttachment]):
        attachment = SlackAttachment()
        callback(attachment)
        self.attachment_list.append(attachment)
        return self

    def http(self, options: dict):
        self.http_options = options
        return self

    def to_dict(self) -> dict:
        message = {}

        if self.content_text:
            message["text"] = self.content_text
        if self.username_value:
            message["username"] = self.username_value
        if self.icon_value:
            if self.icon_value.startswith(":"):
                message["icon_emoji"] = self.icon_value
            else:
                message["icon_url"] = self.icon_value
        if self.channel_value:
            message["channel"] = self.channel_value
        if self.attachment_list:
            message["attachments"] = [a.to_dict() for a in self.attachment_list]

        return message
