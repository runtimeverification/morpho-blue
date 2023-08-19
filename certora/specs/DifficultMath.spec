methods {
    function getMarketId(MorphoHarness.MarketParams) external returns MorphoHarness.Id envfree;
    function getVirtualTotalSupplyAssets(MorphoHarness.Id) external returns uint256 envfree;
    function getVirtualTotalSupplyShares(MorphoHarness.Id) external returns uint256 envfree;
    function MathLib.mulDivDown(uint256 a, uint256 b, uint256 c) internal returns uint256 => summaryMulDivDown(a,b,c);
    function MathLib.mulDivUp(uint256 a, uint256 b, uint256 c) internal returns uint256 => summaryMulDivUp(a,b,c);
    function SafeTransferLib.safeTransfer(address token, address to, uint256 value) internal => NONDET;
    function SafeTransferLib.safeTransferFrom(address token, address from, address to, uint256 value) internal => NONDET;
    function _.onMorphoSupply(uint256 assets, bytes data) external => HAVOC_ECF;
}

function summaryMulDivUp(uint256 x, uint256 y, uint256 d) returns uint256 {
    return require_uint256((x * y + (d - 1)) / d);
}

function summaryMulDivDown(uint256 x, uint256 y, uint256 d) returns uint256 {
    return require_uint256((x * y) / d);
}

// There should be no profit from supply followed immediately by withdraw.
rule supplyWithdraw() {
    MorphoHarness.MarketParams marketParams;
    uint256 assets;
    uint256 shares;
    uint256 suppliedAssets;
    uint256 withdrawnAssets;
    uint256 suppliedShares;
    uint256 withdrawnShares;
    address onbehalf;
    address receiver;
    bytes data;
    env e1;
    env e2;

    require e1.block.timestamp == e2.block.timestamp;

    suppliedAssets, suppliedShares = supply(e1, marketParams, assets, shares, onbehalf, data);

    MorphoHarness.Id id = getMarketId(marketParams);
    assert suppliedAssets * (getVirtualTotalSupplyShares(id) - suppliedShares) >= suppliedShares * (getVirtualTotalSupplyAssets(id) - suppliedAssets);
    assert suppliedAssets * getVirtualTotalSupplyShares(id) >= suppliedShares * getVirtualTotalSupplyAssets(id);

    withdrawnAssets, withdrawnShares = withdraw(e2, marketParams, 0, suppliedShares, onbehalf, receiver);

    assert withdrawnShares == suppliedShares;
    assert withdrawnAssets <= suppliedAssets;
}

// There should be no profit from withdraw followed immediately by supply.
rule withdrawSupply() {
    MorphoHarness.MarketParams marketParams;
    uint256 assets;
    uint256 shares;
    uint256 suppliedAssets;
    uint256 withdrawnAssets;
    uint256 suppliedShares;
    uint256 withdrawnShares;
    address onbehalf;
    address receiver;
    bytes data;
    env e1;
    env e2;

    require e1.block.timestamp == e2.block.timestamp;

    withdrawnAssets, withdrawnShares = withdraw(e2, marketParams, assets, shares, onbehalf, receiver);

    MorphoHarness.Id id = getMarketId(marketParams);
    assert withdrawnAssets * (getVirtualTotalSupplyShares(id) + withdrawnShares) <= withdrawnShares * (getVirtualTotalSupplyAssets(id) + withdrawnAssets);
    assert withdrawnAssets * getVirtualTotalSupplyShares(id) <= withdrawnShares * getVirtualTotalSupplyAssets(id);

    suppliedAssets, suppliedShares = supply(e1, marketParams, withdrawnAssets, 0, onbehalf, data);

    assert suppliedAssets == withdrawnAssets && withdrawnShares >= suppliedShares;
}
