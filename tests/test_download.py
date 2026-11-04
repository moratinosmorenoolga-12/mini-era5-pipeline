import zipfile

from era5qc import download


def test_febrero_no_bisiesto_tiene_28_dias():
    assert len(download.build_request(2023, 2)["day"]) == 28


def test_febrero_bisiesto_tiene_29_dias():
    assert len(download.build_request(2024, 2)["day"]) == 29


def test_request_tiene_variables_horas_y_mes():
    req = download.build_request(2023, 3)
    assert req["month"] == "03"
    assert len(req["variable"]) == 4
    assert req["time"] == ["00:00", "06:00", "12:00", "18:00"]
    assert len(req["day"]) == 31


def test_unpack_descomprime_zip(tmp_path):
    zpath = tmp_path / "download.tmp"
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr("a.nc", b"x")
        z.writestr("b.nc", b"y")
    files = download.unpack(zpath, tmp_path / "out")
    assert [f.name for f in files] == ["a.nc", "b.nc"]
    assert not zpath.exists()


def test_unpack_netcdf_directo(tmp_path):
    path = tmp_path / "download.tmp"
    path.write_bytes(b"no es un zip")
    files = download.unpack(path, tmp_path / "out")
    assert [f.name for f in files] == ["data.nc"]
