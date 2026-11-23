[ComVisible(True)]
public static class XXHash // TypeDefIndex: 60669
{
	// Fields
	private const uint PRIME32_1 = 2654435761;
	private const uint PRIME32_2 = 2246822519;
	private const uint PRIME32_3 = 3266489917;
	private const uint PRIME32_4 = 668265263;
	private const uint PRIME32_5 = 374761393;
	private const ulong PRIME64_1 = 11400714785074694791;
	private const ulong PRIME64_2 = 14029467366897019727;
	private const ulong PRIME64_3 = 1609587929392839161;
	private const ulong PRIME64_4 = 9650029242287828579;
	private const ulong PRIME64_5 = 2870177450012600261;

	// Methods

	// RVA: 0x14932F88 Offset: 0x1492EF88 VA: 0x14932F88
	private static uint XXH_rotl32(uint x, int r) { }

	// RVA: 0x14933004 Offset: 0x1492F004 VA: 0x14933004
	private static ulong XXH_rotl64(ulong x, int r) { }

	// RVA: 0x14933080 Offset: 0x1492F080 VA: 0x14933080
	public static uint XXH32(byte[] input) { }

	// RVA: 0x149330E8 Offset: 0x1492F0E8 VA: 0x149330E8
	public static uint XXH32(byte[] input, uint seed) { }

	// RVA: 0x149335FC Offset: 0x1492F5FC VA: 0x149335FC
	public static uint XXH32(Stream inputStream) { }

	// RVA: 0x14933664 Offset: 0x1492F664 VA: 0x14933664
	public static uint XXH32(Stream inputStream, uint seed) { }

	// RVA: 0x14933AD4 Offset: 0x1492FAD4 VA: 0x14933AD4
	public static ulong XXH64(byte[] input) { }

	// RVA: 0x14933B3C Offset: 0x1492FB3C VA: 0x14933B3C
	public static ulong XXH64(byte[] input, ulong seed) { }

	// RVA: 0x149341C4 Offset: 0x149301C4 VA: 0x149341C4
	public static ulong XXH64(Stream inputStream) { }

	// RVA: 0x1493422C Offset: 0x1493022C VA: 0x1493422C
	public static ulong XXH64(Stream inputStream, ulong seed) { }

	// RVA: 0x149331B8 Offset: 0x1492F1B8 VA: 0x149331B8
	public static uint XXH32(byte[] input, int offset, int length, uint seed) { }

	// RVA: 0x14933C0C Offset: 0x1492FC0C VA: 0x14933C0C
	public static ulong XXH64(byte[] input, int offset, int length, ulong seed) { }

	// RVA: 0x14934CC8 Offset: 0x14930CC8 VA: 0x14934CC8
	public static XXHash.State32 CreateState32() { }

	// RVA: 0x14934DB8 Offset: 0x14930DB8 VA: 0x14934DB8
	public static XXHash.State64 CreateState64() { }

	// RVA: 0x14934D24 Offset: 0x14930D24 VA: 0x14934D24
	public static XXHash.State32 CreateState32(uint seed) { }

	// RVA: 0x14934E14 Offset: 0x14930E14 VA: 0x14934E14
	public static XXHash.State64 CreateState64(ulong seed) { }

	// RVA: 0x14933804 Offset: 0x1492F804 VA: 0x14933804
	public static void ResetState32(XXHash.State32 state, uint seed) { }

	// RVA: 0x14934F78 Offset: 0x14930F78 VA: 0x14934F78
	public static bool UpdateState32(XXHash.State32 state, byte[] input) { }

	// RVA: 0x14935638 Offset: 0x14931638 VA: 0x14935638
	public static bool UpdateState32(XXHash.State32 state, byte[] input, int offset, int length) { }

	// RVA: 0x149338CC Offset: 0x1492F8CC VA: 0x149338CC
	public static bool UpdateState32(XXHash.State32 state, Stream inputStream) { }

	// RVA: 0x149339FC Offset: 0x1492F9FC VA: 0x149339FC
	public static uint DigestState32(XXHash.State32 state) { }

	// RVA: 0x149343CC Offset: 0x149303CC VA: 0x149343CC
	public static void ResetState64(XXHash.State64 state, ulong seed) { }

	// RVA: 0x14935B30 Offset: 0x14931B30 VA: 0x14935B30
	public static bool UpdateState64(XXHash.State64 state, byte[] input) { }

	// RVA: 0x14936194 Offset: 0x14932194 VA: 0x14936194
	public static bool UpdateState64(XXHash.State64 state, byte[] input, int offset, int length) { }

	// RVA: 0x14934494 Offset: 0x14930494 VA: 0x14934494
	public static bool UpdateState64(XXHash.State64 state, Stream inputStream) { }

	// RVA: 0x149345C4 Offset: 0x149305C4 VA: 0x149345C4
	public static ulong DigestState64(XXHash.State64 state) { }

	// RVA: 0x14934EA8 Offset: 0x14930EA8 VA: 0x14934EA8
	internal static void InternalResetState32(XXHash.State32 state, uint seed) { }

	// RVA: 0x14935200 Offset: 0x14931200 VA: 0x14935200
	internal static XXHash.ErrorCode InternalUpdateState32(XXHash.State32 state, byte[] input, int offset, int length) { }

	// RVA: 0x1493582C Offset: 0x1493182C VA: 0x1493582C
	internal static uint InternalDigestState32(XXHash.State32 state) { }

	// RVA: 0x149367A0 Offset: 0x149327A0 VA: 0x149367A0
	private static uint XXH32_round(uint seed, uint input) { }

	// RVA: 0x14935A5C Offset: 0x14931A5C VA: 0x14935A5C
	internal static void InternalResetState64(XXHash.State64 state, ulong seed) { }

	// RVA: 0x14935D18 Offset: 0x14931D18 VA: 0x14935D18
	internal static XXHash.ErrorCode InternalUpdateState64(XXHash.State64 state, byte[] input, int offset, int length) { }

	// RVA: 0x14936388 Offset: 0x14932388 VA: 0x14936388
	internal static ulong InternalDigestState64(XXHash.State64 state) { }

	// RVA: 0x1493691C Offset: 0x1493291C VA: 0x1493691C
	private static ulong XXH64_round(ulong acc, ulong input) { }

	// RVA: 0x149369C0 Offset: 0x149329C0 VA: 0x149369C0
	private static ulong XXH64_mergeRound(ulong acc, ulong val) { }

	// RVA: 0x149347DC Offset: 0x149307DC VA: 0x149347DC
	private static void ThrowArgumentNonNegativeNumber(string paramName) { }

	// RVA: 0x1493469C Offset: 0x1493069C VA: 0x1493469C
	private static void ThrowArrayMultiRank(string paramName) { }

	// RVA: 0x1493473C Offset: 0x1493073C VA: 0x1493473C
	private static void ThrowArrayNonZeroLowerBound(string paramName) { }

	// RVA: 0x1493487C Offset: 0x1493087C VA: 0x1493487C
	private static void ThrowArrayInvalidOffsetAndLength() { }

	// RVA: 0x14936A68 Offset: 0x14932A68 VA: 0x14936A68
	private static void ThrowArrayInvalidOffset(string paramName) { }

	// RVA: 0x14935160 Offset: 0x14931160 VA: 0x14935160
	private static void ThrowStateUninitialized(string paramName) { }
}

// Namespace: Extensions.Data
[ComVisible(True)]
public abstract class XXHash32 : HashAlgorithm // TypeDefIndex: 60670
{
	// Methods

	// RVA: 0x14936C60 Offset: 0x14932C60 VA: 0x14936C60
	protected void .ctor() { }

	// RVA: 0x14936CD4 Offset: 0x14932CD4 VA: 0x14936CD4
	public static XXHash32 Create() { }

	// RVA: 0x14936E18 Offset: 0x14932E18 VA: 0x14936E18
	public static XXHash32 Create(int seed) { }

	// RVA: 0x14936EA4 Offset: 0x14932EA4 VA: 0x14936EA4
	public static XXHash32 Create(uint seed) { }
}

// Namespace: Extensions.Data
[ComVisible(True)]
public sealed class XXHash32CryptoServiceProvider : XXHash32 // TypeDefIndex: 60671
{
	// Fields
	private XXHash.State32 _state; // 0x28

	// Methods

	// RVA: 0x14936FAC Offset: 0x14932FAC VA: 0x14936FAC
	public void .ctor() { }

	// RVA: 0x14936D58 Offset: 0x14932D58 VA: 0x14936D58
	public void .ctor(int seed) { }

	// RVA: 0x14936F30 Offset: 0x14932F30 VA: 0x14936F30
	public void .ctor(uint seed) { }

	// RVA: 0x14937014 Offset: 0x14933014 VA: 0x14937014 Slot: 18
	protected override void HashCore(byte[] array, int ibStart, int cbSize) { }

	// RVA: 0x149370F0 Offset: 0x149330F0 VA: 0x149370F0 Slot: 19
	protected override byte[] HashFinal() { }

	// RVA: 0x1493715C Offset: 0x1493315C VA: 0x1493715C Slot: 20
	public override void Initialize() { }
}

// Namespace: QuickType
public class HandshakeIn // TypeDefIndex: 60672
{
