from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field


@dataclass
class Address:
    email: str
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f'"{self.name}" <{self.email}>'
        return self.email


class Mailable:

    def __init__(self):
        self._to: List[Address] = []
        self._cc: List[Address] = []
        self._bcc: List[Address] = []
        self._from_address: Optional[Address] = None
        self._reply_to: List[Address] = []
        self._subject: Optional[str] = None
        self._view: Optional[str] = None
        self._text_view: Optional[str] = None
        self._html: Optional[str] = None
        self._text: Optional[str] = None
        self._view_data: Dict[str, Any] = {}
        self._attachments: List[Dict[str, Any]] = []
        self._raw_attachments: List[Dict[str, Any]] = []

    def to(
        self, email: Union[str, List[str], Address, List[Address]], name: Optional[str] = None
    ) -> "Mailable":
        if isinstance(email, str):
            self._to.append(Address(email, name))
        elif isinstance(email, Address):
            self._to.append(email)
        elif isinstance(email, list):
            for addr in email:
                if isinstance(addr, str):
                    self._to.append(Address(addr))
                elif isinstance(addr, Address):
                    self._to.append(addr)
        return self

    def cc(
        self, email: Union[str, List[str], Address, List[Address]], name: Optional[str] = None
    ) -> "Mailable":
        if isinstance(email, str):
            self._cc.append(Address(email, name))
        elif isinstance(email, Address):
            self._cc.append(email)
        elif isinstance(email, list):
            for addr in email:
                if isinstance(addr, str):
                    self._cc.append(Address(addr))
                elif isinstance(addr, Address):
                    self._cc.append(addr)
        return self

    def bcc(
        self, email: Union[str, List[str], Address, List[Address]], name: Optional[str] = None
    ) -> "Mailable":
        if isinstance(email, str):
            self._bcc.append(Address(email, name))
        elif isinstance(email, Address):
            self._bcc.append(email)
        elif isinstance(email, list):
            for addr in email:
                if isinstance(addr, str):
                    self._bcc.append(Address(addr))
                elif isinstance(addr, Address):
                    self._bcc.append(addr)
        return self

    def from_address(self, email: Union[str, Address], name: Optional[str] = None) -> "Mailable":
        if isinstance(email, str):
            self._from_address = Address(email, name)
        elif isinstance(email, Address):
            self._from_address = email
        return self

    def reply_to(
        self, email: Union[str, List[str], Address, List[Address]], name: Optional[str] = None
    ) -> "Mailable":
        if isinstance(email, str):
            self._reply_to.append(Address(email, name))
        elif isinstance(email, Address):
            self._reply_to.append(email)
        elif isinstance(email, list):
            for addr in email:
                if isinstance(addr, str):
                    self._reply_to.append(Address(addr))
                elif isinstance(addr, Address):
                    self._reply_to.append(addr)
        return self

    def subject(self, subject: str) -> "Mailable":
        self._subject = subject
        return self

    def view(self, view: str, data: Optional[Dict[str, Any]] = None) -> "Mailable":
        self._view = view
        if data:
            self._view_data.update(data)
        return self

    def text(self, view: str, data: Optional[Dict[str, Any]] = None) -> "Mailable":
        self._text_view = view
        if data:
            self._view_data.update(data)
        return self

    def html(self, html: str) -> "Mailable":
        self._html = html
        return self

    def text_content(self, text: str) -> "Mailable":
        self._text = text
        return self

    def with_data(self, data: Dict[str, Any]) -> "Mailable":
        self._view_data.update(data)
        return self

    def attach(
        self, path: str, name: Optional[str] = None, mime: Optional[str] = None
    ) -> "Mailable":
        self._attachments.append({"path": path, "name": name, "mime": mime})
        return self

    def attach_data(self, data: bytes, name: str, mime: Optional[str] = None) -> "Mailable":
        self._raw_attachments.append({"data": data, "name": name, "mime": mime})
        return self

    def build(self) -> "Mailable":
        return self

    def get_to(self) -> List[Address]:
        return self._to

    def get_cc(self) -> List[Address]:
        return self._cc

    def get_bcc(self) -> List[Address]:
        return self._bcc

    def get_from(self) -> Optional[Address]:
        return self._from_address

    def get_reply_to(self) -> List[Address]:
        return self._reply_to

    def get_subject(self) -> Optional[str]:
        return self._subject

    def get_view(self) -> Optional[str]:
        return self._view

    def get_text_view(self) -> Optional[str]:
        return self._text_view

    def get_html(self) -> Optional[str]:
        return self._html

    def get_text(self) -> Optional[str]:
        return self._text

    def get_view_data(self) -> Dict[str, Any]:
        return self._view_data

    def get_attachments(self) -> List[Dict[str, Any]]:
        return self._attachments

    def get_raw_attachments(self) -> List[Dict[str, Any]]:
        return self._raw_attachments
