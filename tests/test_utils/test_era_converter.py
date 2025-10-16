"""元号変換ユーティリティのテスト"""

import pytest
from datetime import date
from inheritance_calculator_core.utils.era_converter import (
    parse_japanese_date,
    format_japanese_date,
    get_era_name,
    EraConversionError,
)


class TestParseJapaneseDate:
    """parse_japanese_date関数のテスト"""

    def test_parse_reiwa_long_format(self) -> None:
        """令和のlong形式（令和5年10月3日）のパース"""
        result = parse_japanese_date("令和5年10月3日")
        assert result == date(2023, 10, 3)

    def test_parse_reiwa_short_format(self) -> None:
        """令和のshort形式（R5.10.3）のパース"""
        result = parse_japanese_date("R5.10.3")
        assert result == date(2023, 10, 3)

    def test_parse_reiwa_slash_format(self) -> None:
        """令和のslash形式（R5/10/3）のパース"""
        result = parse_japanese_date("R5/10/3")
        assert result == date(2023, 10, 3)

    def test_parse_heisei_long_format(self) -> None:
        """平成のlong形式のパース"""
        result = parse_japanese_date("平成31年4月30日")
        assert result == date(2019, 4, 30)

    def test_parse_heisei_short_format(self) -> None:
        """平成のshort形式のパース"""
        result = parse_japanese_date("H31.4.30")
        assert result == date(2019, 4, 30)

    def test_parse_showa_long_format(self) -> None:
        """昭和のlong形式のパース"""
        result = parse_japanese_date("昭和64年1月7日")
        assert result == date(1989, 1, 7)

    def test_parse_showa_short_format(self) -> None:
        """昭和のshort形式のパース"""
        result = parse_japanese_date("S64.1.7")
        assert result == date(1989, 1, 7)

    def test_parse_taisho_format(self) -> None:
        """大正のパース"""
        result = parse_japanese_date("大正15年12月25日")
        assert result == date(1926, 12, 25)

    def test_parse_meiji_format(self) -> None:
        """明治のパース"""
        result = parse_japanese_date("明治45年7月30日")
        assert result == date(1912, 7, 30)

    def test_parse_western_format_hyphen(self) -> None:
        """西暦形式（ハイフン区切り）のパース"""
        result = parse_japanese_date("2023-10-03")
        assert result == date(2023, 10, 3)

    def test_parse_western_format_slash(self) -> None:
        """西暦形式（スラッシュ区切り）のパース"""
        result = parse_japanese_date("2023/10/3")
        assert result == date(2023, 10, 3)

    def test_parse_western_format_dot(self) -> None:
        """西暦形式（ドット区切り）のパース"""
        result = parse_japanese_date("2023.10.3")
        assert result == date(2023, 10, 3)

    def test_parse_with_fullwidth_numbers(self) -> None:
        """全角数字を含む日付のパース"""
        result = parse_japanese_date("令和５年１０月３日")
        assert result == date(2023, 10, 3)

    def test_parse_single_digit_date(self) -> None:
        """一桁の月日のパース"""
        result = parse_japanese_date("令和1年5月1日")
        assert result == date(2019, 5, 1)

    def test_parse_reiwa_year_1(self) -> None:
        """令和元年（1年）のパース"""
        result = parse_japanese_date("令和1年5月1日")
        assert result == date(2019, 5, 1)

    def test_parse_invalid_format(self) -> None:
        """無効な形式でエラー"""
        with pytest.raises(EraConversionError, match="サポートされていない日付形式"):
            parse_japanese_date("令和五年十月三日")

    def test_parse_invalid_era(self) -> None:
        """存在しない元号でエラー"""
        with pytest.raises(EraConversionError, match="サポートされていない日付形式"):
            parse_japanese_date("X5.10.3")

    def test_parse_before_era_start(self) -> None:
        """元号開始前の日付でエラー"""
        with pytest.raises(EraConversionError, match="開始日.*より前"):
            parse_japanese_date("令和1年4月30日")  # 令和は5月1日開始

    def test_parse_after_era_end(self) -> None:
        """元号終了後の日付でエラー"""
        with pytest.raises(EraConversionError, match="終了日.*より後"):
            parse_japanese_date("平成31年5月1日")  # 平成は4月30日終了

    def test_parse_invalid_date_value(self) -> None:
        """無効な日付値でエラー"""
        with pytest.raises(EraConversionError, match="無効な日付"):
            parse_japanese_date("令和5年13月1日")  # 13月は存在しない


class TestFormatJapaneseDate:
    """format_japanese_date関数のテスト"""

    def test_format_reiwa_long(self) -> None:
        """令和をlong形式でフォーマット"""
        result = format_japanese_date(date(2023, 10, 3), "long")
        assert result == "令和5年10月3日"

    def test_format_reiwa_short(self) -> None:
        """令和をshort形式でフォーマット"""
        result = format_japanese_date(date(2023, 10, 3), "short")
        assert result == "R5.10.3"

    def test_format_reiwa_slash(self) -> None:
        """令和をslash形式でフォーマット"""
        result = format_japanese_date(date(2023, 10, 3), "slash")
        assert result == "R5/10/3"

    def test_format_heisei(self) -> None:
        """平成をフォーマット"""
        result = format_japanese_date(date(2019, 4, 30), "long")
        assert result == "平成31年4月30日"

    def test_format_showa(self) -> None:
        """昭和をフォーマット"""
        result = format_japanese_date(date(1989, 1, 7), "long")
        assert result == "昭和64年1月7日"

    def test_format_taisho(self) -> None:
        """大正をフォーマット"""
        result = format_japanese_date(date(1926, 12, 25), "long")
        assert result == "大正15年12月25日"

    def test_format_meiji(self) -> None:
        """明治をフォーマット"""
        result = format_japanese_date(date(1912, 7, 30), "long")
        assert result == "明治45年7月30日"

    def test_format_reiwa_year_1(self) -> None:
        """令和元年（1年）をフォーマット"""
        result = format_japanese_date(date(2019, 5, 1), "long")
        assert result == "令和1年5月1日"

    def test_format_before_meiji(self) -> None:
        """明治以前の日付でエラー"""
        with pytest.raises(EraConversionError, match="明治以前"):
            format_japanese_date(date(1868, 1, 24), "long")

    def test_format_invalid_format_type(self) -> None:
        """無効なフォーマットタイプでエラー"""
        with pytest.raises(ValueError, match="不明なフォーマット"):
            format_japanese_date(date(2023, 10, 3), "invalid")  # type: ignore


class TestGetEraName:
    """get_era_name関数のテスト"""

    def test_get_reiwa(self) -> None:
        """令和の元号名を取得"""
        result = get_era_name(date(2023, 10, 3))
        assert result == "令和"

    def test_get_heisei(self) -> None:
        """平成の元号名を取得"""
        result = get_era_name(date(2019, 4, 30))
        assert result == "平成"

    def test_get_showa(self) -> None:
        """昭和の元号名を取得"""
        result = get_era_name(date(1989, 1, 7))
        assert result == "昭和"

    def test_get_taisho(self) -> None:
        """大正の元号名を取得"""
        result = get_era_name(date(1926, 12, 25))
        assert result == "大正"

    def test_get_meiji(self) -> None:
        """明治の元号名を取得"""
        result = get_era_name(date(1912, 7, 30))
        assert result == "明治"

    def test_get_era_transition_day(self) -> None:
        """元号切り替え日の判定"""
        # 平成最終日
        assert get_era_name(date(2019, 4, 30)) == "平成"
        # 令和初日
        assert get_era_name(date(2019, 5, 1)) == "令和"

    def test_get_before_meiji(self) -> None:
        """明治以前の日付でエラー"""
        with pytest.raises(EraConversionError, match="明治以前"):
            get_era_name(date(1868, 1, 24))


class TestRoundTripConversion:
    """往復変換（パース→フォーマット）のテスト"""

    def test_roundtrip_reiwa(self) -> None:
        """令和の往復変換"""
        original = "令和5年10月3日"
        parsed = parse_japanese_date(original)
        formatted = format_japanese_date(parsed, "long")
        assert formatted == original

    def test_roundtrip_different_formats(self) -> None:
        """異なる形式間の往復変換"""
        short_format = "R5.10.3"
        parsed = parse_japanese_date(short_format)
        long_format = format_japanese_date(parsed, "long")
        assert long_format == "令和5年10月3日"

        # 逆方向
        parsed2 = parse_japanese_date(long_format)
        short_format2 = format_japanese_date(parsed2, "short")
        assert short_format2 == short_format

    def test_roundtrip_western_to_era(self) -> None:
        """西暦から元号への変換"""
        western = "2023-10-03"
        parsed = parse_japanese_date(western)
        era_format = format_japanese_date(parsed, "long")
        assert era_format == "令和5年10月3日"
