from typing_extensions import override
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.evaluation.financial_gain_loss_evaluation import (
    FinancialGainLossEvaluation,
    GainsAndLosses,
    add_changes,
    split_to_gains_and_losses,
)
from traces_analyzer.evaluation.securify_properties_evaluation import (
    SecurifyProperties,
    SecurifyPropertiesEvaluation,
)
from traces_parser.datatypes.hexstring import HexString


class OverallProperties(SecurifyProperties):
    attacker_gain_and_victim_loss: bool
    attacker_eoa_gain: bool
    attacker_eoa_loss: bool
    attacker_bot_gain: bool
    attacker_bot_loss: bool
    victim_gain: bool
    victim_loss: bool


class OverallPropertiesEvaluation(Evaluation):
    @property
    @override
    def _type_key(self):
        return "overall_properties"

    @property
    @override
    def _type_name(self):
        return "Properties"

    def __init__(
        self,
        attackers: tuple[HexString, HexString],
        victim: HexString,
        securify_properties_evaluations: tuple[
            SecurifyPropertiesEvaluation, SecurifyPropertiesEvaluation
        ],
        financial_gain_loss_evaluations: tuple[
            FinancialGainLossEvaluation, FinancialGainLossEvaluation
        ],
    ):
        super().__init__()
        self._securify_properties = merge_securify_properties(
            securify_properties_evaluations[0].get_properties(),
            securify_properties_evaluations[1].get_properties(),
        )
        self._gains_and_losses = merge_financial_gain_loss(
            financial_gain_loss_evaluations[0].get_gains_and_losses(),
            financial_gain_loss_evaluations[1].get_gains_and_losses(),
        )
        self._props = compute_props(
            self._securify_properties, self._gains_and_losses, attackers, victim
        )
        self.attackers = attackers
        self.victim = victim

    @override
    def _dict_report(self) -> dict:
        return {
            "properties": dict(self._props),
            "attacker_EOA": self.attackers[0].with_prefix(),
            "attacker_potential_bot": self.attackers[1].with_prefix(),
            "victim": self.victim.with_prefix(),
            "overall_gains_and_losses": dict(self._gains_and_losses),
        }

    @override
    def _cli_report(self) -> str:
        return f"""Attacker gain and victim loss: {self._props['attacker_gain_and_victim_loss']}
TOD Transfer: {self._props['TOD_Transfer']}
TOD Amount: {self._props['TOD_Amount']}
TOD Receiver: {self._props['TOD_Receiver']}"""


def merge_securify_properties(
    props_a: SecurifyProperties, props_b: SecurifyProperties
) -> SecurifyProperties:
    return {
        "TOD_Transfer": props_a["TOD_Transfer"] or props_b["TOD_Transfer"],
        "TOD_Amount": props_a["TOD_Amount"] or props_b["TOD_Amount"],
        "TOD_Receiver": props_a["TOD_Receiver"] or props_b["TOD_Receiver"],
    }


def merge_financial_gain_loss(a: GainsAndLosses, b: GainsAndLosses):
    overall_changes = add_changes(a["gains"], a["losses"], b["gains"], b["losses"])
    return split_to_gains_and_losses(overall_changes)


def compute_props(
    securify_props: SecurifyProperties,
    gains_and_losses: GainsAndLosses,
    attackers: tuple[HexString, HexString],
    victim: HexString,
) -> OverallProperties:
    attacker_eoa_gain, attacker_eoa_loss = check_gain_loss(
        gains_and_losses, attackers[0]
    )
    attacker_bot_gain, attacker_bot_loss = check_gain_loss(
        gains_and_losses, attackers[1]
    )
    victim_gain, victim_loss = check_gain_loss(gains_and_losses, victim)

    overall_prop = (
        (attacker_eoa_gain and not attacker_eoa_loss)
        or (attacker_bot_gain and not attacker_bot_loss)
    ) and (victim_loss and not victim_gain)

    return {
        "TOD_Transfer": securify_props["TOD_Transfer"],
        "TOD_Amount": securify_props["TOD_Amount"],
        "TOD_Receiver": securify_props["TOD_Receiver"],
        "attacker_gain_and_victim_loss": overall_prop,
        "attacker_eoa_gain": attacker_eoa_gain,
        "attacker_eoa_loss": attacker_eoa_loss,
        "attacker_bot_gain": attacker_bot_gain,
        "attacker_bot_loss": attacker_bot_loss,
        "victim_gain": victim_gain,
        "victim_loss": victim_loss,
    }


def check_gain_loss(gains_and_losses: GainsAndLosses, address: HexString):
    gains = address.with_prefix().lower() in gains_and_losses["gains"]
    losses = address.with_prefix().lower() in gains_and_losses["losses"]
    return gains, losses
