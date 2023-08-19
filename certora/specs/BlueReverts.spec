methods {
    function owner() external returns address envfree;
    function getTotalSupplyAssets(MorphoHarness.Id) external returns uint256 envfree;
    function getTotalBorrowAssets(MorphoHarness.Id) external returns uint256 envfree;
    function getTotalSupplyShares(MorphoHarness.Id) external returns uint256 envfree;
    function getTotalBorrowShares(MorphoHarness.Id) external returns uint256 envfree;
    function isAuthorized(address, address) external returns bool envfree;
    function getLastUpdate(MorphoHarness.Id) external returns uint256 envfree;
    function isLltvEnabled(uint256) external returns bool envfree;
    function isIrmEnabled(address) external returns bool envfree;

    function getMarketId(MorphoHarness.MarketParams) external returns MorphoHarness.Id envfree;
    function MAX_FEE() external returns uint256 envfree;
    function WAD() external returns uint256 envfree;
}

definition isCreated(MorphoHarness.Id id) returns bool =
    (getLastUpdate(id) != 0);

ghost mapping(MorphoHarness.Id => mathint) sumCollateral
{
    init_state axiom (forall MorphoHarness.Id id. sumCollateral[id] == 0);
}
hook Sstore user[KEY MorphoHarness.Id id][KEY address owner].collateral uint128 newAmount (uint128 oldAmount) STORAGE {
    sumCollateral[id] = sumCollateral[id] - oldAmount + newAmount;
}

definition emptyMarket(MorphoHarness.Id id) returns bool =
    getTotalSupplyAssets(id) == 0 &&
    getTotalSupplyShares(id) == 0 &&
    getTotalBorrowAssets(id) == 0 &&
    getTotalBorrowShares(id) == 0 &&
    sumCollateral[id] == 0;

definition exactlyOneZero(uint256 assets, uint256 shares) returns bool =
    (assets == 0 && shares != 0) || (assets != 0 && shares == 0);

// This invariant catches bugs when not checking that the market is created with lastUpdate.
invariant notInitializedEmpty(MorphoHarness.Id id)
    !isCreated(id) => emptyMarket(id);

invariant zeroDoesNotAuthorize(address authorized)
    !isAuthorized(0, authorized)
{
    preserved setAuthorization(address _authorized, bool _newAuthorization) with (env e) {
        require e.msg.sender != 0;
    }
}

rule setOwnerRevertCondition(env e, address newOwner) {
    address oldOwner = owner();
    setOwner@withrevert(e, newOwner);
    assert lastReverted <=> e.msg.value != 0 || e.msg.sender != oldOwner;
}

rule enableIrmRevertCondition(env e, address irm) {
    address oldOwner = owner();
    enableIrm@withrevert(e, irm);
    assert lastReverted <=> e.msg.value != 0 || e.msg.sender != oldOwner;
}

rule enableLltvRevertCondition(env e, uint256 lltv) {
    address oldOwner = owner();
    enableLltv@withrevert(e, lltv);
    assert lastReverted <=> e.msg.value != 0 || e.msg.sender != oldOwner || lltv >= WAD();
}

// setFee can also revert if the accrueInterests reverts.
rule setFeeInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 newFee) {
    address oldOwner = owner();
    MorphoHarness.Id id = getMarketId(marketParams);
    setFee@withrevert(e, marketParams, newFee);
    bool hasReverted = lastReverted;
    assert e.msg.value != 0 || e.msg.sender != oldOwner || !isCreated(id) || newFee > MAX_FEE() => hasReverted;
}

rule setFeeRecipientRevertCondition(env e, address recipient) {
    address oldOwner = owner();
    setFeeRecipient@withrevert(e, recipient);
    assert lastReverted <=> e.msg.value != 0 || e.msg.sender != oldOwner;
}

rule createMarketRevertCondition(env e, MorphoHarness.MarketParams marketParams) {
    MorphoHarness.Id id = getMarketId(marketParams);
    createMarket@withrevert(e, marketParams);
    assert lastReverted <=> e.msg.value != 0 || !isIrmEnabled(marketParams.irm) || !isLltvEnabled(marketParams.lltv) || getLastUpdate(id) != 0;
}

rule supplyInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, uint256 shares, address onBehalf, bytes b) {
    supply@withrevert(e, marketParams, assets, shares, onBehalf, b);
    assert !exactlyOneZero(assets, shares) || onBehalf == 0 => lastReverted;
}

rule withdrawInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver) {
    require e.msg.sender != 0;
    requireInvariant zeroDoesNotAuthorize(e.msg.sender);
    withdraw@withrevert(e, marketParams, assets, shares, onBehalf, receiver);
    assert !exactlyOneZero(assets, shares) || onBehalf == 0 => lastReverted;
}

rule borrowInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver) {
    require e.msg.sender != 0;
    requireInvariant zeroDoesNotAuthorize(e.msg.sender);
    borrow@withrevert(e, marketParams, assets, shares, onBehalf, receiver);
    assert !exactlyOneZero(assets, shares) || onBehalf == 0 => lastReverted;
}

rule repayInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, uint256 shares, address onBehalf, bytes b) {
    repay@withrevert(e, marketParams, assets, shares, onBehalf, b);
    assert !exactlyOneZero(assets, shares) || onBehalf == 0 => lastReverted;
}

rule supplyCollateralInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, address onBehalf, bytes b) {
    supplyCollateral@withrevert(e, marketParams, assets, onBehalf, b);
    assert assets == 0 || onBehalf == 0 => lastReverted;
}

rule withdrawCollateralInputValidation(env e, MorphoHarness.MarketParams marketParams, uint256 assets, address onBehalf, address receiver) {
    require e.msg.sender != 0;
    requireInvariant zeroDoesNotAuthorize(e.msg.sender);
    withdrawCollateral@withrevert(e, marketParams, assets, onBehalf, receiver);
    assert assets == 0 || onBehalf == 0 => lastReverted;
}

rule liquidateInputValidation(env e, MorphoHarness.MarketParams marketParams, address borrower, uint256 seized, bytes b) {
    liquidate@withrevert(e, marketParams, borrower, seized, b);
    assert seized == 0 => lastReverted;
}
