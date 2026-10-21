from dataclasses import dataclass


@dataclass
class TransferResult:
    success: bool
    transaction_id: str | None
    message: str


@dataclass
class VendorVerificationResult:
    verified: bool
    vendor: str
    message: str


@dataclass
class EmailResult:
    success: bool
    recipient: str
    message: str


class FakeBankAPI:
    """
    Simulated banking API for the AgentShield hackathon demo.

    This represents the dangerous external tool that AgentShield
    must protect.
    """

    def verify_vendor(
        self,
        vendor: str,
    ) -> VendorVerificationResult:
        print(
            f"[FAKE BANK] VERIFYING VENDOR: {vendor}"
        )

        return VendorVerificationResult(
            verified=True,
            vendor=vendor,
            message=f"Vendor {vendor} verified successfully",
        )

    def transfer_money(
        self,
        recipient: str,
        amount: float,
    ) -> TransferResult:
        print(
            f"[FAKE BANK] EXECUTING TRANSFER: "
            f"₹{amount:,.2f} -> {recipient}"
        )

        return TransferResult(
            success=True,
            transaction_id="TX-DEMO-001",
            message=f"Successfully transferred ₹{amount:,.2f} to {recipient}",
        )

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> EmailResult:
        print(
            f"[FAKE EMAIL] SENDING EMAIL TO: {recipient}"
        )
        print(
            f"[FAKE EMAIL] SUBJECT: {subject}"
        )

        return EmailResult(
            success=True,
            recipient=recipient,
            message=f"Email sent successfully to {recipient}",
        )